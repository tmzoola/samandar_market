import asyncio
import logging
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import anyio
import uvicorn
from admin import setup_admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.error_handlers import *
from core.exceptions import AppException
from core.kafka_publisher import publisher as kafka_publisher
from api.v1.user import router as user_router
from api.v1.organization import router as organization_router

from core.minio import minio_client
from core.redis import redis_client
from db.session import session_factory
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from logging_config import setup_logging
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

scheduler = AsyncIOScheduler()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")



@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        setup_logging()
        setup_admin(app)

        try:
            await redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise RuntimeError("Redis is required for scheduler operation") from e

        await kafka_publisher.start()
        app.state.publisher = kafka_publisher

        logger.info("✅ App starting up...")

        if not scheduler.running:
            schedule_jobs(scheduler)
            scheduler.start()
            logger.info("🧹 Scheduler started and jobs scheduled.")

        yield

    except Exception as e:
        logger.exception(f"Startup error: {e}")
        raise

    finally:
        logger.info("🔴 Shutting down app...")
        try:
            if scheduler.running:
                await asyncio.wait_for(scheduler.shutdown(wait=False), timeout=5)
                logger.info("Scheduler shut down.")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

        try:
            if kafka_publisher:
                await asyncio.wait_for(kafka_publisher.stop(), timeout=5)
                logger.info("Kafka publisher stopped.")
        except Exception as e:
            logger.error(f"Error stopping Kafka publisher: {e}")


app = FastAPI(
    title="UzAssets",
    docs_url="/api/v1/uzassets/swagger/",
    openapi_url="/api/v1/uzassets/openapi.json",
    redoc_url=None,
    version="0.1.0",
    description="XS Auth is a FastAPI application for user authentication and management.",
    lifespan=lifespan,
)


def schedule_jobs(scheduler: AsyncIOScheduler):
    #room for scheduled tasks
    pass



# Register handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def https_middleware(request: Request, call_next):
    x_forwarded_proto = request.headers.get("x-forwarded-proto")
    if settings.APP_MODE == "PRODUCTION":
        is_production = "uzassets.imv.uz" in str(request.url)
    else:
        is_production = "uzassetsdev.imv.uz" in str(request.url)

    if x_forwarded_proto == "https" or is_production:
        scope = dict(request.scope)
        scope["scheme"] = "https"

        if "x-forwarded-host" in request.headers:
            scope["headers"] = [
                (b"host", request.headers["x-forwarded-host"].encode()),
                *[(k, v) for k, v in request.scope["headers"] if k != b"host"],
            ]
        request = Request(scope, request.receive)

    response = await call_next(request)

    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "upgrade-insecure-requests; "
        "default-src 'self' https: http:; "  # Added http:
        "script-src 'self' https: 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' https: 'unsafe-inline'; "
        "style-src-elem 'self' https: 'unsafe-inline'; "
        "img-src 'self' https: data: blob:; "
        "font-src 'self' https: data:; "
        "connect-src 'self' https: http:;"  # Added http:
        "frame-ancestors 'self';"
    )

    return response


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "uzassets.imv.uz",
        "uzassetsdev.imv.uz",
        "localhost",
        "127.0.0.1",
        "uzassets_backend",
        "",
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)

all_routers = [
    user_router,
    organization_router,
]
for router in all_routers:
    app.include_router(router, prefix="/api/v1/uzassets")


@app.get("/health")
async def health_check():
    # Kafka check
    if not await kafka_publisher.check_kafka_cluster_health():
        logger.error("Kafka is unreachable.")
        return JSONResponse(status_code=503, content={"status": "kafka-unreachable"})

    try:
        pong = await redis_client.ping()
        redis_ok = pong is True
        logger.info("Redis is reachable")
    except Exception as e:
        logger.error(f"Redis error: {e}")
        return JSONResponse(status_code=503, content={"status": "redis-unreachable"})

    # MinIO check
    # try:
    #     await anyio.to_thread.run_sync(minio_client.client.list_buckets)
    #     logger.info("MinIO is reachable")
    # except Exception as e:
    #     logger.error(f"MinIO error: {e}")
    #     return JSONResponse(status_code=503, content={"status": "minio-unreachable"})

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            logger.info("PostgreSQL is reachable")
    except Exception as e:
        logger.error(f"PostgreSQL error: {e}")
        return JSONResponse(status_code=503, content={"status": "postgres-unreachable"})

    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9080,
        log_level="info",
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
