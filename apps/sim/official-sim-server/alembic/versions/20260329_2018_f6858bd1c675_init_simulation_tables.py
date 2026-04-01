"""init_simulation_tables

Revision ID: f6858bd1c675
Revises:
Create Date: 2026-03-29 20:18:58.555771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6858bd1c675'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id BLOB PRIMARY KEY,
            run_code VARCHAR(64) UNIQUE NOT NULL,
            template_id BLOB,
            platform VARCHAR(32) NOT NULL,
            account_id BLOB,
            status VARCHAR(32) NOT NULL DEFAULT 'created',
            strict_mode VARCHAR(1) DEFAULT '1',
            push_enabled VARCHAR(1) DEFAULT '1',
            seed VARCHAR(128),
            current_step INTEGER DEFAULT 0,
            metadata_json TEXT DEFAULT '{}',
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS simulation_events (
            id BLOB PRIMARY KEY,
            run_id BLOB NOT NULL,
            step_no INTEGER NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            source_type VARCHAR(32),
            payload_json TEXT DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS state_snapshots (
            id BLOB PRIMARY KEY,
            run_id BLOB NOT NULL,
            step_no INTEGER NOT NULL,
            auth_state_json TEXT DEFAULT '{}',
            order_state_json TEXT DEFAULT '{}',
            shipment_state_json TEXT DEFAULT '{}',
            after_sale_state_json TEXT DEFAULT '{}',
            conversation_state_json TEXT DEFAULT '{}',
            push_state_json TEXT DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS push_events (
            id BLOB PRIMARY KEY,
            run_id BLOB NOT NULL,
            step_no INTEGER NOT NULL,
            platform VARCHAR(32) NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            status VARCHAR(32) DEFAULT 'created',
            headers_json TEXT DEFAULT '{}',
            body_json TEXT DEFAULT '{}',
            sent_at TIMESTAMP,
            acked_at TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id BLOB PRIMARY KEY,
            run_id BLOB NOT NULL,
            step_no INTEGER NOT NULL,
            platform VARCHAR(32) NOT NULL,
            artifact_type VARCHAR(64) NOT NULL,
            route_key VARCHAR(128),
            request_headers_json TEXT DEFAULT '{}',
            request_body_json TEXT DEFAULT '{}',
            response_headers_json TEXT DEFAULT '{}',
            response_body_json TEXT DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_reports (
            id BLOB PRIMARY KEY,
            run_id BLOB NOT NULL,
            report_version VARCHAR(32) DEFAULT '1.0',
            summary_json TEXT DEFAULT '{}',
            expected_json TEXT DEFAULT '{}',
            actual_json TEXT DEFAULT '{}',
            issues_json TEXT DEFAULT '[]',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_simulation_runs_run_code ON simulation_runs(run_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_simulation_runs_platform ON simulation_runs(platform)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_simulation_runs_platform_status ON simulation_runs(platform, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_simulation_events_run_step ON simulation_events(run_id, step_no)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_state_snapshots_run_step ON state_snapshots(run_id, step_no)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_push_events_run_step ON push_events(run_id, step_no)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_push_events_platform ON push_events(platform)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_artifacts_run_step ON artifacts(run_id, step_no)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_artifacts_platform ON artifacts(platform)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS evaluation_reports")
    op.execute("DROP TABLE IF EXISTS artifacts")
    op.execute("DROP TABLE IF EXISTS push_events")
    op.execute("DROP TABLE IF EXISTS state_snapshots")
    op.execute("DROP TABLE IF EXISTS simulation_events")
    op.execute("DROP TABLE IF EXISTS simulation_runs")
