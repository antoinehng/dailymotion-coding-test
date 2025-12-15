from abc import ABC
from abc import abstractmethod


class EmailService(ABC):
    """Port for sending emails."""

    @abstractmethod
    async def send_activation_code(self, email: str, activation_code: str) -> None:
        """Send activation code to user's email.

        Args:
            email: The recipient's email address
            activation_code: The 4-digit activation code to send
        """
        ...
