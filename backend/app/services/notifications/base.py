from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class NotificationMessage:
    recipient: str  # Phone number with country code or email
    subject: str
    body: str
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResponse:
    success: bool
    provider: str
    message_id: str
    error: Optional[str] = None
    share_url: Optional[str] = None  # e.g. https://wa.me/?text=... for instant UI sharing


class NotificationProvider(ABC):
    """Abstract interface for multi-channel dispatch (WhatsApp, Email, SMS)."""

    @abstractmethod
    async def send_message(self, message: NotificationMessage) -> NotificationResponse:
        """Send outbound notification."""
        pass
