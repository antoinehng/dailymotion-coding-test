from typing import ClassVar

from src.domain.common.public_id import PublicId


class UserPublicId(PublicId):
    """Public identifier for a user."""

    PREFIX: ClassVar[str] = "usr"
