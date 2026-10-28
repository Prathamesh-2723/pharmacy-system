from app.services.notifications.base import (
    NotificationProvider,
    NotificationMessage,
    NotificationResponse,
)
from app.services.notifications.console import ConsoleWhatsAppProvider
from app.services.notifications.whatsapp_stub import WhatsAppCloudApiStub
from app.services.notifications.email_adapter import EmailAdapter


def get_notification_provider(channel: str = "whatsapp") -> NotificationProvider:
    if channel.lower() == "email":
        return EmailAdapter()
    return ConsoleWhatsAppProvider()


__all__ = [
    "NotificationProvider",
    "NotificationMessage",
    "NotificationResponse",
    "ConsoleWhatsAppProvider",
    "WhatsAppCloudApiStub",
    "EmailAdapter",
    "get_notification_provider",
]
