from enum import Enum
from enum import StrEnum
from typing import TypeVar


class EnumHelper:
    TEnum = TypeVar("TEnum", bound=Enum)

    @staticmethod
    def merge(name: str, *enums: type[TEnum]) -> Enum | StrEnum:
        """
        Merges multiple enums into a single enum.
        Works with both Enum and StrEnum.

        Args:
            *enums: The enums to merge.
            name: The name for the combined enum.

        Returns:
            A new enum class that combines all input enums.
        """
        combined_dict: dict[str, str | int] = {}
        enum_type = (
            StrEnum if all(issubclass(enum, StrEnum) for enum in enums) else Enum
        )

        for enum in enums:
            combined_dict.update({k: v.value for k, v in enum.__members__.items()})

        return enum_type(name, combined_dict)
