"""管理员业务逻辑 — 用户管理 + 数据看板统计."""

from datetime import datetime, timedelta, timezone

from app.domain.enums import UserRole
from app.domain.models import make_user
from app.repositories.json_repository import JsonRepository
from app.security.passwords import hash_password


class AdminService:
    """管理员服务 — 用户管理与数据看板."""

    def __init__(self, repo: JsonRepository) -> None:
        self._repo = repo

    # ── 用户管理 ──

    def list_users(self) -> list[dict]:
        """返回全部用户列表."""
        return self._repo.list_users()

    def create_user(self, username: str, email: str, password: str, role: str) -> dict | str:
        """创建用户 — 检查重名/重邮箱后调用工厂创建."""
        if self._repo.find_user_by_username(username):
            return "username_taken"
        if self._repo.find_user_by_email(email):
            return "email_taken"

        try:
            role_enum = UserRole(role)
        except ValueError:
            return "invalid_role"

        user = make_user(
            self._repo._store,
            username,
            email,
            hash_password(password),
            role_enum,
        )
        return self._repo.create_user(user)

    def toggle_user(self, user_id: str, is_active: bool) -> dict | None:
        """启用/禁用用户 — 禁用时踢出所有会话."""
        updated = self._repo.update_user(user_id, {"is_active": is_active})
        if updated and not is_active:
            self._repo.destroy_sessions_by_user(user_id)
        return updated

    # ── 数据看板 ──

    def get_stats(self) -> dict:
        """聚合全量数据生成看板统计."""
        data = self._repo._store.read()
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=30)

        contracts = data.get("contracts", [])
        total = len(contracts)

        # 状态分布
        status_distribution: dict[str, int] = {}
        for c in contracts:
            s = c.get("status", "unknown")
            status_distribution[s] = status_distribution.get(s, 0) + 1

        # 即将到期（30 天内，且状态为 active 或 signed）
        expiring_soon = 0
        for c in contracts:
            expires_at = c.get("expires_at")
            if expires_at and c.get("status") in ("active", "signed"):
                try:
                    expire_date = datetime.fromisoformat(expires_at)
                    if now <= expire_date <= cutoff:
                        expiring_soon += 1
                except (ValueError, TypeError):
                    pass

        # 审批通过率
        records = data.get("approval_records", [])
        decided = [r for r in records if r.get("decision") != "pending"]
        approved_count = sum(1 for r in decided if r.get("decision") == "approved")
        approval_rate = round(approved_count / len(decided), 4) if decided else 0.0

        return {
            "total_contracts": total,
            "status_distribution": status_distribution,
            "expiring_soon": expiring_soon,
            "approval_rate": approval_rate,
            "total_users": len(data.get("users", [])),
            "total_templates": len(data.get("templates", [])),
        }
