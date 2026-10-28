import logging
import uuid
from app.services.notifications.base import (
    NotificationProvider,
    NotificationMessage,
    NotificationResponse,
)

logger = logging.getLogger("expiryos.email")


class EmailAdapter(NotificationProvider):
    """Email adapter for outbound return dispatch and credit alerts."""

    async def send_message(self, message: NotificationMessage) -> NotificationResponse:
        logger.info(
            f"[EMAIL DISPATCH] To: {message.recipient} | Subject: {message.subject}"
        )
        return NotificationResponse(
            success=True,
            provider="email_adapter",
            message_id=f"email-{uuid.uuid4().hex[:12]}",
        )
