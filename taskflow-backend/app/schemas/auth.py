from pydantic import BaseModel

from app.schemas.user import UserPublic


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
