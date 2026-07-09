"""FastAPI 应用入口."""
import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, contracts, internal, templates, admin
from app.bootstrap import bootstrap_admin
from app.config import get_settings
from app.storage.json_store import JsonFileStore

# 确保 JS/CSS 文件的 MIME 类型正确（Windows 下 mimetypes 可能识别错误）
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router)
app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(internal.router)
app.include_router(templates.router)
app.include_router(admin.router)

# 静态文件
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/pages", StaticFiles(directory=str(frontend_dir / "pages")), name="pages")
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")


@app.on_event("startup")
def on_startup():
    store = JsonFileStore(settings.DATA_FILE)
    bootstrap_admin(store)


@app.get("/")
def root():
    return RedirectResponse(url="/pages/public/login.html")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
