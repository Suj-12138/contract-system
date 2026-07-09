from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    contract_id: str | None
    is_read: bool
    created_at: str
