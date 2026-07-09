"""配置加载 — 环境变量 → Settings 对象."""

import os
from functools import lru_cache


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "企业合同管理系统")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    DATA_FILE: str = os.getenv("CONTRACT_DATA_FILE", "backend/data/store.json")
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
