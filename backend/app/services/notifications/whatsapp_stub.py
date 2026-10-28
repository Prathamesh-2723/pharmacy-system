import logging
import uuid
from app.services.notifications.base import (
    NotificationProvider,
    NotificationMessage,
    NotificationResponse,
)

logger = logging.getLogger("expiryos.whatsapp_cloud")


class WhatsAppCloudApiStub(NotificationProvider):
    """
    Production stub for Meta WhatsApp Business Cloud API.
    Ready for credentials: WHATSAPP_API_TOKEN, WHATSAPP_PHONE_NUMBER_ID, Graph API v20.0.
    """

    def __init__(self, token: str = "", phone_number_id: str = ""):
        self.token = token
        self.phone_number_id = phone_number_id

    async def send_message(self, message: NotificationMessage) -> NotificationResponse:
        logger.info(
            f"[WhatsApp Cloud API Stub] Outbound payload to {message.recipient} via PhoneID {self.phone_number_id}. Ready for live webhook."
        )
        return NotificationResponse(
            success=True,
            provider="whatsapp_cloud_stub",
            message_id=f"wamid.HBgL{uuid.uuid4().hex[:16]}",
        )
