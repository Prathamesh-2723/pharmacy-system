from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


TENANT_TABLES = [
    "users",
    "distributors",
    "distributor_rules",
    "products",
    "batches",
    "purchase_invoices",
    "return_requests",
    "return_request_items",
    "return_status_events",
    "credit_notes",
    "notifications",
]


async def set_tenant_context(session: AsyncSession, tenant_id: Optional[str]) -> None:
    """
    Sets PostgreSQL session setting 'app.current_tenant' for the current transaction.
    This activates the PostgreSQL Row-Level Security (RLS) policies.
    """
    if tenant_id:
        # Safe parameterized execution
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
    else:
        await session.execute(
            text("SELECT set_config('app.current_tenant', '', true)")
        )


def get_rls_sql_commands() -> list[str]:
    """Generates the DDL SQL statements to enable and force RLS on all tenant tables."""
    commands = []
    for tbl in TENANT_TABLES:
        commands.append(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        commands.append(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")
        commands.append(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = '{tbl}' AND policyname = '{tbl}_tenant_isolation'
                ) THEN
                    CREATE POLICY {tbl}_tenant_isolation ON {tbl}
                    FOR ALL
                    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
                    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));
                END IF;
            END $$;
            """
        )
    return commands
