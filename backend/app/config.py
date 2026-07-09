"""配置加载 — 环境变量 → Settings 对象."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 项目根目录 = backend/（即 app/ 的父目录）
_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "企业合同管理系统")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    DATA_FILE: str = os.getenv(
        "CONTRACT_DATA_FILE",
        str(_BACKEND_DIR / "data" / "store.json"),
    )
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "contract_session")
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "8"))
    EXPIRY_WARN_DAYS: int = int(os.getenv("EXPIRY_WARN_DAYS", "30"))
    INITIAL_ADMIN_USERNAME: str = os.getenv("INITIAL_ADMIN_USERNAME", "")
    INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "")
    INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
