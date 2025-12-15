from enum import StrEnum
from typing import ClassVar
from typing import NewType

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr

from src.domain.common.public_id import PublicId
from src.domain.user.value_objects.password_hash import PasswordHash

UserId = NewType("UserId", int)


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"


class UserPublicId(PublicId):
    """Public identifier for a user."""

    PREFIX: ClassVar[str] = "usr"


class User(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UserId
    public_id: UserPublicId
    email: EmailStr
    password_hash: PasswordHash
    status: UserStatus
