import urllib.parse
import uuid
import logging
from app.services.notifications.base import (
    NotificationProvider,
    NotificationMessage,
    NotificationResponse,
)

logger = logging.getLogger("expiryos.notifications")


class ConsoleWhatsAppProvider(NotificationProvider):
    """
    Mock & interactive WhatsApp provider.
    Logs outbound notification payload cleanly to console/logs,
    and returns a pre-filled direct WhatsApp Web share URL (wa.me)
    so pharmacy operators can 1-click dispatch to the distributor's phone!
    """

    async def send_message(self, message: NotificationMessage) -> NotificationResponse:
        msg_id = f"mock-wa-{uuid.uuid4().hex[:10]}"
        cleaned_phone = message.recipient.replace("+", "").replace("-", "").replace(" ", "")
        encoded_text = urllib.parse.quote(message.body)
        share_url = f"https://wa.me/{cleaned_phone}?text={encoded_text}" if cleaned_phone else f"https://wa.me/?text={encoded_text}"

        logger.info(
            f"\n--- [WHATSAPP DISPATCH] ---\n"
            f"To: {message.recipient}\n"
            f"Subject: {message.subject}\n"
            f"Share Link: {share_url}\n"
            f"Body:\n{message.body}\n"
            f"---------------------------\n"
        )

        return NotificationResponse(
            success=True,
            provider="console_whatsapp",
            message_id=msg_id,
            share_url=share_url,
        )
