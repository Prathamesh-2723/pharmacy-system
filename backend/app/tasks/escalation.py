import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.return_request import ReturnRequest, ReturnStatusEvent
from app.models.distributor import Distributor
from app.tasks.celery_app import celery_app


async def check_overdue_credit_slas_logic(session) -> List[Dict[str, Any]]:
    """
    Identifies return requests in SENT / ACKNOWLEDGED / PICKED_UP states
    whose credit_sla_deadline has passed without credit note settlement,
    and logs an escalation status event.
    """
    now = datetime.now(timezone.utc)
    pending_statuses = ["SENT", "ACKNOWLEDGED", "PICKED_UP"]

    query = (
        select(ReturnRequest)
        .options(selectinload(ReturnRequest.distributor))
        .where(
            ReturnRequest.status.in_(pending_statuses),
            ReturnRequest.credit_sla_deadline.isnot(None),
            ReturnRequest.credit_sla_deadline < now,
        )
    )
    overdue_returns = (await session.scalars(query)).all()
    escalated = []

    for ret in overdue_returns:
        event = ReturnStatusEvent(
            return_request_id=ret.id,
            tenant_id=ret.tenant_id,
            from_status=ret.status,
            to_status=ret.status,  # Remains in current operational status but logged with SLA overdue trigger
            trigger="CRON_SLA_CHECK",
            comment=f"Credit SLA breached! Distributor {ret.distributor.name if ret.distributor else ''} deadline was {ret.credit_sla_deadline.strftime('%Y-%m-%d')}.",
            metadata_json={"overdue": True, "deadline": ret.credit_sla_deadline.isoformat()},
        )
        session.add(event)
        escalated.append({
            "return_request_id": ret.id,
            "return_request_no": ret.return_request_no,
            "distributor_id": ret.distributor_id,
            "distributor_name": ret.distributor.name if ret.distributor else "Unknown",
            "deadline": str(ret.credit_sla_deadline),
        })

    if escalated:
        await session.commit()

    return escalated


@celery_app.task(name="app.tasks.escalation.check_overdue_credit_slas")
def check_overdue_credit_slas():
    async def _runner():
        async with async_session_factory() as session:
            return await check_overdue_credit_slas_logic(session)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _runner()).result()
    else:
        return asyncio.run(_runner())
