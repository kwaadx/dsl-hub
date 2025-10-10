-- =========================================================
-- Downgrade for 9f0b7b2c6f3a_init_upgrade.sql
-- PostgreSQL 17+
-- =========================================================

DO
$$
DECLARE
    has_version_table boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'alembic_version'
          AND table_schema IN ('api', 'public')
    ) INTO has_version_table;

    IF NOT has_version_table THEN
        EXECUTE 'DROP SCHEMA IF EXISTS api CASCADE';
        EXECUTE 'DROP EXTENSION IF EXISTS citext';
        EXECUTE 'DROP EXTENSION IF EXISTS pgcrypto';
    ELSE
        IF to_regclass('api.flow') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_flow_updated ON api.flow';
        END IF;
        IF to_regclass('api.pipeline') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_pipeline_updated ON api.pipeline';
        END IF;
        IF to_regclass('api.schema_channel') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_schema_channel_updated ON api.schema_channel';
        END IF;
        IF to_regclass('api.schema_def') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_schema_def_updated ON api.schema_def';
        END IF;
        IF to_regclass('api.schema_compat_rule') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_schema_compat_rule_updated ON api.schema_compat_rule';
        END IF;
        IF to_regclass('api.schema_upgrade_plan') IS NOT NULL THEN
            EXECUTE 'DROP TRIGGER IF EXISTS trg_schema_upgrade_plan_updated ON api.schema_upgrade_plan';
        END IF;

        EXECUTE 'DROP VIEW IF EXISTS api.job_run_all';
        EXECUTE 'DROP VIEW IF EXISTS api.flow_active_pipeline';

        EXECUTE 'DROP TABLE IF EXISTS api.conversation_session CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.flow_checkpoint CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.pipeline_upgrade_run CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.pipeline_generation_run CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.summary_run CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.thread_summary CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.pipeline_summary CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.flow_summary CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.pipeline_validation_issue CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.schema_upgrade_plan CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.schema_compat_rule CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.pipeline CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.schema_def CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.schema_channel CASCADE';
        EXECUTE 'DROP TABLE IF EXISTS api.flow CASCADE';

        EXECUTE 'DROP FUNCTION IF EXISTS api.set_updated_at()';

        EXECUTE 'DROP TYPE IF EXISTS api.pipeline_status';
        EXECUTE 'DROP TYPE IF EXISTS api.run_status';
        EXECUTE 'DROP TYPE IF EXISTS api.issue_severity';
        EXECUTE 'DROP TYPE IF EXISTS api.summary_scope';

    END IF;
END
$$;
