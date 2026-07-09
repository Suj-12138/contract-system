from app.domain.enums import UserRole
from app.domain.models import make_user
from app.repositories.json_repository import JsonRepository
from app.security.passwords import hash_password, verify_password
from app.security.sessions import generate_token, make_session


class AuthService:
    def __init__(self, repo: JsonRepository):
        self.repo = repo

    def login(self, username_or_email: str, password: str) -> tuple[dict, str] | str:
        """成功返回 (user, raw_token)，失败返回错误码."""
        if "@" in username_or_email:
            user = self.repo.find_user_by_email(username_or_email)
        else:
            user = self.repo.find_user_by_username(username_or_email)

        if not user or not verify_password(user["password_hash"], password):
            return "invalid_credentials"
        if not user.get("is_active", True):
            return "account_disabled"

        raw_token = generate_token()
        session = make_session(user["id"], raw_token)
        self.repo.create_session(session)
        return user, raw_token

    def register(self, username: str, email: str, password: str, role: str) -> dict | str:
        if self.repo.find_user_by_username(username):
            return "username_taken"
        if self.repo.find_user_by_email(email):
            return "email_taken"

        try:
            role_enum = UserRole(role)
        except ValueError:
            return "invalid_role"

        user = make_user(self.repo._store, username, email, hash_password(password), role_enum)
        return self.repo.create_user(user)

    def logout(self, token_hash: str) -> None:
        self.repo.destroy_session_by_token(token_hash)

    def get_me(self, user_id: str) -> dict | None:
        return self.repo.find_user_by_id(user_id)
