from urllib.parse import urljoin

from admin.auth import AdminAuth
from admin.views.user import UserAdminView
from admin.views.organization import OrganizationAdminView
from db.session import engine
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from models.user import User
from models.organization import Organization
from starlette_admin.contrib.sqla import Admin


def setup_admin(app: FastAPI):
    base_url = "/api/v1/uzassets/dashboard/"
    admin_base_url = "https://uzassets.imv.uz/api/v1/uzassets/dashboard"

    # Create a custom admin class that forces HTTPS
    class HTTPSAdmin(Admin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._base_url = admin_base_url

        def _build_url(self, path: str) -> str:
            """Build URL with forced HTTPS"""
            if path.startswith(("http://", "https://")):
                return path
            return urljoin(self._base_url, path.lstrip("/"))

    admin = HTTPSAdmin(
        engine,
        title="UzAssets Dashboard",
        auth_provider=AdminAuth(),
        base_url=base_url,
        statics_dir="statics/starlette_admin",
    )
    admin.add_view(UserAdminView(User))
    admin.add_view(OrganizationAdminView(Organization))
    admin.mount_to(app)

    from pathlib import Path

    static_dir = Path("statics/starlette_admin")
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)

    class HTTPSStaticFiles(StaticFiles):
        async def __call__(self, scope, receive, send):
            if scope.get("type") == "http":
                scope = dict(scope)
                scope["scheme"] = "https"
                headers = dict(scope.get("headers", []))
                scope["headers"] = [(b"host", b"xizmatdev.imv.uz")] + [
                    (k, v) for k, v in scope.get("headers", []) if k != b"host"
                ]
            await super().__call__(scope, receive, send)

    app.mount(
        "/api/v1/uzassets/dashboard/statics",
        HTTPSStaticFiles(directory="statics/starlette_admin"),
        name="admin-statics",
    )
