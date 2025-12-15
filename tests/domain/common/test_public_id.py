from dataclasses import FrozenInstanceError
from typing import ClassVar
from uuid import UUID
from uuid import uuid7

import pytest

from src.domain.common.public_id import PublicId
from src.domain.user.public_id import UserPublicId


class TestPublicIdInitialization:
    """Test PublicId initialization."""

    def test_init_with_valid_prefix_and_uuid(self) -> None:
        """Test initialization with valid prefix and UUID."""
        uuid = uuid7()
        public_id = UserPublicId(prefix="usr", uuid_v7=uuid)

        assert public_id.prefix == "usr"
        assert public_id.uuid_v7 == uuid

    def test_init_with_invalid_prefix_raises_value_error(self) -> None:
        """Test that invalid prefix raises ValueError."""
        uuid = uuid7()

        with pytest.raises(
            ValueError, match="Invalid prefix: expected 'usr', got 'invalid'"
        ):
            UserPublicId(prefix="invalid", uuid_v7=uuid)

    def test_init_with_wrong_prefix_raises_value_error(self) -> None:
        """Test that wrong prefix raises ValueError."""
        uuid = uuid7()

        with pytest.raises(
            ValueError, match="Invalid prefix: expected 'usr', got 'pay'"
        ):
            UserPublicId(prefix="pay", uuid_v7=uuid)


class TestPublicIdGenerate:
    """Test PublicId.generate() classmethod."""

    def test_generate_creates_new_public_id(self) -> None:
        """Test that generate() creates a new PublicId with correct prefix."""
        public_id = UserPublicId.generate()

        assert isinstance(public_id, UserPublicId)
        assert public_id.prefix == "usr"
        assert isinstance(public_id.uuid_v7, UUID)

    def test_generate_creates_unique_ids(self) -> None:
        """Test that generate() creates unique IDs."""
        id1 = UserPublicId.generate()
        id2 = UserPublicId.generate()

        assert id1 != id2
        assert id1.uuid_v7 != id2.uuid_v7


class TestPublicIdFromString:
    """Test PublicId.from_string() classmethod."""

    def test_from_string_with_valid_format(self) -> None:
        """Test parsing valid string format."""
        uuid = uuid7()
        value = f"usr_{uuid}"

        public_id = UserPublicId.from_string(value)

        assert isinstance(public_id, UserPublicId)
        assert public_id.prefix == "usr"
        assert public_id.uuid_v7 == uuid

    def test_from_string_roundtrip(self) -> None:
        """Test that from_string() and __str__() are inverse operations."""
        original = UserPublicId.generate()
        string_repr = str(original)
        parsed = UserPublicId.from_string(string_repr)

        assert parsed == original
        assert parsed.prefix == original.prefix
        assert parsed.uuid_v7 == original.uuid_v7

    def test_from_string_with_invalid_prefix_raises_value_error(self) -> None:
        """Test that invalid prefix in string raises ValueError."""
        uuid = uuid7()
        value = f"invalid_{uuid}"

        # The error from __init__ is caught and wrapped by from_string
        with pytest.raises(ValueError, match="Invalid UserPublicId format"):
            UserPublicId.from_string(value)

    def test_from_string_with_invalid_uuid_format_raises_value_error(self) -> None:
        """Test that invalid UUID format raises ValueError."""
        value = "usr_invalid-uuid"

        with pytest.raises(ValueError, match="Invalid UserPublicId format"):
            UserPublicId.from_string(value)

    def test_from_string_with_missing_separator_raises_value_error(self) -> None:
        """Test that missing separator raises ValueError."""
        value = "usr123456"

        with pytest.raises(ValueError, match="Invalid UserPublicId format"):
            UserPublicId.from_string(value)

    def test_from_string_with_empty_string_raises_value_error(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid UserPublicId format"):
            UserPublicId.from_string("")

    def test_from_string_with_only_prefix_raises_value_error(self) -> None:
        """Test that string with only prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid UserPublicId format"):
            UserPublicId.from_string("usr_")


class TestPublicIdStringRepresentation:
    """Test PublicId string representations."""

    def test_str_returns_expected_format(self) -> None:
        """Test that __str__() returns prefix_uuid format."""
        uuid = uuid7()
        public_id = UserPublicId(prefix="usr", uuid_v7=uuid)

        assert str(public_id) == f"usr_{uuid}"

    def test_repr_returns_expected_format(self) -> None:
        """Test that __repr__() returns expected format."""
        uuid = uuid7()
        public_id = UserPublicId(prefix="usr", uuid_v7=uuid)

        repr_str = repr(public_id)
        assert repr_str.startswith("UserPublicId(")
        assert "prefix='usr'" in repr_str
        assert f"uuid_v7={uuid}" in repr_str


class TestPublicIdEquality:
    """Test PublicId equality."""

    def test_equality_with_same_values(self) -> None:
        """Test that two PublicIds with same values are equal."""
        uuid = uuid7()
        id1 = UserPublicId(prefix="usr", uuid_v7=uuid)
        id2 = UserPublicId(prefix="usr", uuid_v7=uuid)

        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_inequality_with_different_uuids(self) -> None:
        """Test that two PublicIds with different UUIDs are not equal."""
        id1 = UserPublicId.generate()
        id2 = UserPublicId.generate()

        assert id1 != id2

    def test_inequality_with_different_types(self) -> None:
        """Test that PublicIds of different types are not equal."""

        # Create a different PublicId type for testing
        class PaymentPublicId(PublicId):
            PREFIX: ClassVar[str] = "pay"

        user_id = UserPublicId.generate()
        payment_id = PaymentPublicId.generate()

        assert user_id != payment_id
        assert not (user_id == payment_id)  # noqa: SIM201 - explicitly checking equality

    def test_equality_with_non_public_id_returns_false(self) -> None:
        """Test that equality with non-PublicId object returns False."""
        public_id = UserPublicId.generate()

        assert public_id != "not_a_public_id"
        assert public_id != 123  # noqa: PLR2004
        assert public_id != None  # noqa: E711


class TestPublicIdHash:
    """Test PublicId hashing."""

    def test_hash_is_consistent(self) -> None:
        """Test that hash is consistent for same object."""
        public_id = UserPublicId.generate()
        hash1 = hash(public_id)
        hash2 = hash(public_id)

        assert hash1 == hash2

    def test_hash_is_different_for_different_objects(self) -> None:
        """Test that hash is different for different objects."""
        id1 = UserPublicId.generate()
        id2 = UserPublicId.generate()

        assert hash(id1) != hash(id2)

    def test_hash_includes_class_type(self) -> None:
        """Test that hash includes class type (different types have different hashes)."""

        # Create a different PublicId type for testing
        class PaymentPublicId(PublicId):
            PREFIX: ClassVar[str] = "pay"

        uuid = uuid7()
        user_id = UserPublicId(prefix="usr", uuid_v7=uuid)
        payment_id = PaymentPublicId(prefix="pay", uuid_v7=uuid)

        # Even with same UUID, different types should have different hashes
        assert hash(user_id) != hash(payment_id)

    def test_hashable_in_set(self) -> None:
        """Test that PublicId can be used in sets."""
        id1 = UserPublicId.generate()
        id2 = UserPublicId.generate()
        id3 = UserPublicId.generate()

        public_id_set = {id1, id2, id3}

        assert len(public_id_set) == 3  # noqa: PLR2004
        assert id1 in public_id_set
        assert id2 in public_id_set
        assert id3 in public_id_set

    def test_hashable_in_dict(self) -> None:
        """Test that PublicId can be used as dictionary key."""
        id1 = UserPublicId.generate()
        id2 = UserPublicId.generate()

        public_id_dict = {id1: "user1", id2: "user2"}

        assert public_id_dict[id1] == "user1"
        assert public_id_dict[id2] == "user2"


class TestPublicIdImmutability:
    """Test PublicId immutability."""

    def test_frozen_model_cannot_be_modified(self) -> None:
        """Test that PublicId is immutable (frozen)."""
        public_id = UserPublicId.generate()

        with pytest.raises(FrozenInstanceError):
            public_id.prefix = "modified"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            public_id.uuid_v7 = uuid7()  # type: ignore[misc]


class TestPublicIdPrefixValidator:
    """Test PublicId prefix validator."""

    def test_validator_rejects_wrong_prefix(self) -> None:
        """Test that __post_init__ validator rejects wrong prefix."""
        uuid = uuid7()

        # The validator should catch this during initialization
        with pytest.raises(ValueError, match="Invalid prefix"):
            UserPublicId(prefix="wrong", uuid_v7=uuid)
