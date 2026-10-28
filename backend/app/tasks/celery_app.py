from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "expiryos",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.expiry_scanner",
        "app.tasks.escalation",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "daily-expiry-scan": {
            "task": "app.tasks.expiry_scanner.run_daily_expiry_scan",
            "schedule": crontab(hour=1, minute=0),  # Runs at 01:00 AM daily
        },
        "daily-credit-sla-check": {
            "task": "app.tasks.escalation.check_overdue_credit_slas",
            "schedule": crontab(hour=2, minute=0),  # Runs at 02:00 AM daily
        },
    },
)
