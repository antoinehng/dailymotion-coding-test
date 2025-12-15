from enum import StrEnum
from enum import auto

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


class HealthcheckStatus(StrEnum):
    OK = auto()
    KO = auto()


class HealthcheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    status: HealthcheckStatus
    timestamp: str
    message: str
