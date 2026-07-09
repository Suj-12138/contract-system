from datetime import datetime, timezone, timedelta
from app.domain.models import make_message
from app.repositories.json_repository import JsonRepository
from app.config import get_settings


class MessageService:
    def __init__(self, repo: JsonRepository):
        self.repo = repo

    def list_for_user(self, user_id: str, is_read: bool | None) -> list[dict]:
        return self.repo.list_messages_by_user(user_id, is_read)

    def unread_count(self, user_id: str) -> int:
        return self.repo.unread_message_count(user_id)

    def mark_read(self, message_id: str, user_id: str) -> dict | str:
        messages = self.repo.list_messages_by_user(user_id)
        for m in messages:
            if m["id"] == message_id:
                return self.repo.mark_message_read(message_id)
        return "not_found"

    def check_expiry_and_notify(self) -> int:
        """扫描即将到期合同并发送提醒，返回发送消息数."""
        settings = get_settings()
        warn_days = settings.EXPIRY_WARN_DAYS
        threshold = datetime.now(timezone.utc) + timedelta(days=warn_days)
        threshold_str = threshold.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = self.repo._store.read()
        count = 0
        for c in data["contracts"]:
            if c["status"] != "active" or not c.get("expires_at"):
                continue
            try:
                expires = datetime.fromisoformat(c["expires_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if expires <= threshold.replace(tzinfo=timezone.utc):
                # 检查是否已发过提醒（简单去重：检查最近 7 天内是否有同合同的消息）
                recent = [m for m in data["messages"]
                          if m["contract_id"] == c["id"] and "即将到期" in m["title"]
                          and (datetime.now(timezone.utc) - datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))).days < 7]
                if not recent:
                    msg = make_message(
                        self.repo._store, c["handler_id"],
                        "合同即将到期",
                        f"合同「{c['title']}」将于 {c['expires_at']} 到期，请及时处理。",
                        c["id"],
                    )
                    self.repo.create_message(msg)
                    count += 1
        return count
