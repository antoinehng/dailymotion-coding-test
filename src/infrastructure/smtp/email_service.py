from src.application.registration.ports.email_service import EmailService
from src.infrastructure.logging.logger import getLogger

logger = getLogger(__name__)


class LoggerEmailService(EmailService):
    """Logger adapter for email service (logs to terminal instead of sending emails)."""

    async def send_activation_code(self, email: str, activation_code: str) -> None:
        """Send activation code to user's email (logs to terminal).

        Args:
            email: The recipient's email address
            activation_code: The 4-digit activation code to send
        """
        logger.info(
            "Sending activation code email",
            extra={
                "email": email,
                "activation_code": activation_code,
            },
        )
        # Print to terminal for visibility
        print(f"\n{'=' * 60}")
        print("ACTIVATION CODE EMAIL")
        print(f"{'=' * 60}")
        print(f"To: {email}")
        print(f"Activation Code: {activation_code}")
        print(f"{'=' * 60}\n")
