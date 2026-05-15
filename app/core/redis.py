import redis.asyncio as redis
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

# Redis job store connection
jobstores = {
    "default": RedisJobStore(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        jobs_key="apscheduler.jobs",
        run_times_key="apscheduler.run_times",
    )
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
