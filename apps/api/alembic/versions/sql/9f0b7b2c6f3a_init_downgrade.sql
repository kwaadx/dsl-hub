-- =========================================================
-- Downgrade for 9f0b7b2c6f3a_init_upgrade.sql
-- Reverts the initial DSL-Hub Authoring DB schema
-- PostgreSQL 17+
-- =========================================================

-- Note:
-- We drop dependent objects in a safe reverse-dependency order.
-- Tables are dropped with CASCADE to remove FKs, triggers, and indexes.
-- Helper trigger functions are dropped at the end.
-- Extensions created by the upgrade are intentionally left intact
-- (pgcrypto, pg_trgm, citext) to avoid impacting other schemas.

-- ---------- Views ----------
DROP VIEW IF EXISTS flow_active_pipeline;

-- ---------- Tables (reverse order) ----------
DROP TABLE IF EXISTS compat_rule CASCADE;
DROP TABLE IF EXISTS pipeline_upgrade_run CASCADE;
DROP TABLE IF EXISTS schema_upgrade_plan CASCADE;
DROP TABLE IF EXISTS prompt_template CASCADE;
DROP TABLE IF EXISTS summary_run CASCADE;
DROP TABLE IF EXISTS context_snapshot CASCADE;
DROP TABLE IF EXISTS thread_summary CASCADE;
DROP TABLE IF EXISTS flow_summary CASCADE;
DROP TABLE IF EXISTS agent_log CASCADE;
DROP TABLE IF EXISTS validation_issue CASCADE;
DROP TABLE IF EXISTS generation_run CASCADE;
DROP TABLE IF EXISTS pipeline CASCADE;
DROP TABLE IF EXISTS schema_channel CASCADE;
DROP TABLE IF EXISTS schema_def CASCADE;
DROP TABLE IF EXISTS message CASCADE;
DROP TABLE IF EXISTS thread CASCADE;
DROP TABLE IF EXISTS flow CASCADE;

-- ---------- Trigger/helper functions ----------
DROP FUNCTION IF EXISTS thread_context_snapshot_same_flow();
DROP FUNCTION IF EXISTS thread_result_pipeline_same_flow();
DROP FUNCTION IF EXISTS summary_run_same_flow();
DROP FUNCTION IF EXISTS generation_run_same_flow();
DROP FUNCTION IF EXISTS context_snapshot_same_flow();
DROP FUNCTION IF EXISTS flow_summary_last_msg_same_flow();
DROP FUNCTION IF EXISTS message_parent_same_thread();
DROP FUNCTION IF EXISTS pipeline_sync_schema_version();
DROP FUNCTION IF EXISTS set_archived_ts();
DROP FUNCTION IF EXISTS set_updated_at();
