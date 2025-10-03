"""
M6: DB invariants and performance indexes
- pg_trgm extension
- unique published per flow (partial unique index)
- check constraints for statuses/roles/formats
- indexes for common queries
- TRGM index on pipeline content text
"""
from __future__ import annotations

from alembic import op

revision = "20251002_01_constraints_indexes"
down_revision = "20251001_00_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Partial unique: one published pipeline per flow
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_pipeline_published_per_flow
        ON pipeline(flow_id)
        WHERE is_published = true;
        """
    )

    # CHECK constraints with defensive existence checks
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'thread_status_ck'
            ) THEN
                ALTER TABLE thread ADD CONSTRAINT thread_status_ck
                CHECK (status IN ('NEW','IN_PROGRESS','SUCCESS','FAILED','ARCHIVED'));
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'message_role_ck'
            ) THEN
                ALTER TABLE message ADD CONSTRAINT message_role_ck
                CHECK (role IN ('user','assistant','system','tool'));
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'message_format_ck'
            ) THEN
                ALTER TABLE message ADD CONSTRAINT message_format_ck
                CHECK (format IN ('text','markdown','json','buttons','card'));
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'pipeline_status_ck'
            ) THEN
                ALTER TABLE pipeline ADD CONSTRAINT pipeline_status_ck
                CHECK (status IN ('draft','published'));
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'generation_run_status_ck'
            ) THEN
                ALTER TABLE generation_run ADD CONSTRAINT generation_run_status_ck
                CHECK (status IN ('queued','running','succeeded','failed'));
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'generation_run_stage_ck'
            ) THEN
                ALTER TABLE generation_run ADD CONSTRAINT generation_run_stage_ck
                CHECK (length(coalesce(stage,'')::text) > 0);
            END IF;
        END$$;
        """
    )

    # Performance indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_flow_created_at
        ON pipeline(flow_id, created_at DESC);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_message_thread_created_at
        ON message(thread_id, created_at);
        """
    )

    # TRGM index on pipeline content text
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_content_trgm
        ON pipeline USING gin ((content::text) gin_trgm_ops);
        """
    )


def downgrade() -> None:
    # Drop TRGM content index
    op.execute("DROP INDEX IF EXISTS idx_pipeline_content_trgm;")

    # Drop performance indexes
    op.execute("DROP INDEX IF EXISTS idx_message_thread_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_pipeline_flow_created_at;")

    # Drop constraints
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'generation_run_stage_ck') THEN
                ALTER TABLE generation_run DROP CONSTRAINT generation_run_stage_ck;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'generation_run_status_ck') THEN
                ALTER TABLE generation_run DROP CONSTRAINT generation_run_status_ck;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pipeline_status_ck') THEN
                ALTER TABLE pipeline DROP CONSTRAINT pipeline_status_ck;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'message_format_ck') THEN
                ALTER TABLE message DROP CONSTRAINT message_format_ck;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'message_role_ck') THEN
                ALTER TABLE message DROP CONSTRAINT message_role_ck;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'thread_status_ck') THEN
                ALTER TABLE thread DROP CONSTRAINT thread_status_ck;
            END IF;
        END $$;
        """
    )

    # Drop partial unique
    op.execute("DROP INDEX IF EXISTS uq_pipeline_published_per_flow;")
