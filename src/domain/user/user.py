from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr

from src.domain.user.password_hash import PasswordHash
from src.domain.user.public_id import UserPublicId
from src.domain.user.status import UserStatus


class User(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: int
    public_id: UserPublicId
    email: EmailStr
    password_hash: PasswordHash
    status: UserStatus
