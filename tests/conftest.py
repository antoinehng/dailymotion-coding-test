import os
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def set_bcrypt_cost_factor() -> Generator[None, None, None]:  # noqa: UP043 - Explicit even if None because of yield and static type checker
    """Set lower bcrypt cost factor for faster tests.

    Bcrypt default cost factor is 12 (2^12 = 4096 rounds), which is secure but slow.
    For tests, we use cost factor 4 (2^4 = 16 rounds) which is ~250x faster while
    still testing the actual bcrypt functionality.
    """
    os.environ["BCRYPT_COST_FACTOR"] = "4"
    yield
    # Cleanup: restore default if needed
    os.environ.pop("BCRYPT_COST_FACTOR", None)
