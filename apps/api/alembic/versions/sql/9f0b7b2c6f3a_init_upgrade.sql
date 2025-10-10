-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

-- Schema
CREATE SCHEMA IF NOT EXISTS api;
SET search_path TO api, public;

DO
$$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at') THEN
            CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS
            $f$
            BEGIN
                NEW.updated_at := now();
                RETURN NEW;
            END
            $f$ LANGUAGE plpgsql;
        END IF;
    END
$$;

DO
$$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pipeline_status') THEN
            CREATE TYPE pipeline_status AS ENUM ('DRAFT','REVIEWED','ACTIVE','DEPRECATED','FAILED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_status') THEN
            CREATE TYPE run_status AS ENUM ('PENDING','RUNNING','SUCCESS','FAILED','CANCELED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'issue_severity') THEN
            CREATE TYPE issue_severity AS ENUM ('INFO','WARN','ERROR');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'summary_scope') THEN
            CREATE TYPE summary_scope AS ENUM ('PIPELINE','FLOW','THREAD');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status') THEN
            CREATE TYPE session_status AS ENUM ('OPEN','CLOSED','IDLE');
        END IF;
    END
$$;

CREATE TABLE IF NOT EXISTS flow
(
    id                 uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    slug               citext      NOT NULL UNIQUE,
    name               text        NOT NULL,
    active_pipeline_id uuid        NULL,
    summary_id         uuid        NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);
DROP TRIGGER IF EXISTS trg_flow_updated ON flow;
CREATE TRIGGER trg_flow_updated
    BEFORE UPDATE
    ON flow
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pipeline
(
    id                uuid PRIMARY KEY         DEFAULT gen_random_uuid(),
    flow_id           uuid            NOT NULL REFERENCES flow (id) ON DELETE CASCADE,
    status            pipeline_status NOT NULL,
    revision          int             NOT NULL DEFAULT 1,
    schema_def_id     uuid            NOT NULL,
    schema_version    text            NOT NULL,
    schema_hash       text            NOT NULL,
    content           jsonb           NOT NULL,
    validation_report jsonb           NULL,
    summary_id        uuid            NULL,
    activated_at      timestamptz     NULL,
    superseded_by     uuid            NULL,
    created_at        timestamptz     NOT NULL DEFAULT now(),
    updated_at        timestamptz     NOT NULL DEFAULT now(),
    CONSTRAINT pipeline_content_is_object CHECK (jsonb_typeof(content) = 'object')
);
CREATE INDEX IF NOT EXISTS idx_pipeline_flow ON pipeline (flow_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_schema_def ON pipeline (schema_def_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_pipeline_per_flow ON pipeline (flow_id) WHERE status = 'ACTIVE';
DROP TRIGGER IF EXISTS trg_pipeline_updated ON pipeline;
CREATE TRIGGER trg_pipeline_updated
    BEFORE UPDATE
    ON pipeline
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

ALTER TABLE flow
    ADD CONSTRAINT fk_flow_active_pipeline
        FOREIGN KEY (active_pipeline_id) REFERENCES pipeline (id) ON DELETE SET NULL;

ALTER TABLE pipeline
    ADD CONSTRAINT fk_pipeline_superseded_by
        FOREIGN KEY (superseded_by) REFERENCES pipeline (id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS schema_channel
(
    id         uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    key        citext      NOT NULL UNIQUE,
    name       text        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
DROP TRIGGER IF EXISTS trg_schema_channel_updated ON schema_channel;
CREATE TRIGGER trg_schema_channel_updated
    BEFORE UPDATE
    ON schema_channel
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS schema_def
(
    id         uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    channel_id uuid        NULL REFERENCES schema_channel (id) ON DELETE SET NULL,
    version    text        NOT NULL,
    hash       text        NOT NULL UNIQUE,
    content    jsonb       NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_schema_def_channel_version ON schema_def (channel_id, version);
DROP TRIGGER IF EXISTS trg_schema_def_updated ON schema_def;
CREATE TRIGGER trg_schema_def_updated
    BEFORE UPDATE
    ON schema_def
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

ALTER TABLE pipeline
    ADD CONSTRAINT fk_pipeline_schema_def
        FOREIGN KEY (schema_def_id) REFERENCES schema_def (id) ON DELETE RESTRICT;

CREATE TABLE IF NOT EXISTS schema_compat_rule
(
    id            uuid PRIMARY KEY        DEFAULT gen_random_uuid(),
    schema_def_id uuid           NOT NULL REFERENCES schema_def (id) ON DELETE CASCADE,
    code          text           NOT NULL,
    severity      issue_severity NOT NULL,
    description   text           NOT NULL,
    condition     jsonb          NOT NULL,
    action        jsonb          NULL,
    created_at    timestamptz    NOT NULL DEFAULT now(),
    updated_at    timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT ux_schema_compat_rule UNIQUE (schema_def_id, code)
);
DROP TRIGGER IF EXISTS trg_schema_compat_rule_updated ON schema_compat_rule;
CREATE TRIGGER trg_schema_compat_rule_updated
    BEFORE UPDATE
    ON schema_compat_rule
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS schema_upgrade_plan
(
    id                 uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    from_schema_def_id uuid        NOT NULL REFERENCES schema_def (id) ON DELETE RESTRICT,
    to_schema_def_id   uuid        NOT NULL REFERENCES schema_def (id) ON DELETE RESTRICT,
    strategy           text        NOT NULL DEFAULT 'transform',
    plan               jsonb       NOT NULL DEFAULT '{}'::jsonb,
    notes              text        NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ux_schema_upgrade_pair UNIQUE (from_schema_def_id, to_schema_def_id),
    CONSTRAINT ck_schema_upgrade_plan_strategy CHECK (strategy in ('transform', 'no_change', 'manual_only', 'deprecated'))
);
DROP TRIGGER IF EXISTS trg_schema_upgrade_plan_updated ON schema_upgrade_plan;
CREATE TRIGGER trg_schema_upgrade_plan_updated
    BEFORE UPDATE
    ON schema_upgrade_plan
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pipeline_validation_issue
(
    id          uuid PRIMARY KEY        DEFAULT gen_random_uuid(),
    pipeline_id uuid           NOT NULL REFERENCES pipeline (id) ON DELETE CASCADE,
    code        text           NOT NULL,
    severity    issue_severity NOT NULL,
    path        text           NULL,
    message     text           NOT NULL,
    details     jsonb          NULL,
    created_at  timestamptz    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_issue_pipeline ON pipeline_validation_issue (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_issue_severity ON pipeline_validation_issue (severity);

CREATE TABLE IF NOT EXISTS pipeline_summary
(
    id          uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    pipeline_id uuid        NOT NULL UNIQUE REFERENCES pipeline (id) ON DELETE CASCADE,
    title       text        NULL,
    text        text        NOT NULL,
    facts       jsonb       NULL,
    created_by  text        NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS flow_summary
(
    id         uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    flow_id    uuid        NOT NULL UNIQUE REFERENCES flow (id) ON DELETE CASCADE,
    title      text        NULL,
    text       text        NOT NULL,
    facts      jsonb       NULL,
    created_by text        NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE flow
    ADD CONSTRAINT fk_flow_summary
        FOREIGN KEY (summary_id) REFERENCES flow_summary (id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS thread_summary
(
    id          uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    thread_id   text        NOT NULL UNIQUE,
    flow_id     uuid        NOT NULL REFERENCES flow (id) ON DELETE CASCADE,
    pipeline_id uuid        NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    title       text        NULL,
    text        text        NOT NULL,
    facts       jsonb       NULL,
    created_by  text        NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_thread_summary_flow ON thread_summary (flow_id);
CREATE INDEX IF NOT EXISTS idx_thread_summary_pipeline ON thread_summary (pipeline_id);

ALTER TABLE pipeline
    ADD CONSTRAINT fk_pipeline_summary
        FOREIGN KEY (summary_id) REFERENCES pipeline_summary (id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS flow_checkpoint
(
    thread_id   text PRIMARY KEY,
    flow_id     uuid        NOT NULL REFERENCES flow (id) ON DELETE CASCADE,
    pipeline_id uuid        NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    checkpoint  jsonb       NOT NULL,
    metadata    jsonb       NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_checkpoint_flow ON flow_checkpoint (flow_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_pipeline ON flow_checkpoint (pipeline_id);

CREATE TABLE IF NOT EXISTS conversation_session
(
    id               uuid PRIMARY KEY        DEFAULT gen_random_uuid(),
    flow_id          uuid           NOT NULL REFERENCES flow (id) ON DELETE CASCADE,
    thread_id        text           NOT NULL UNIQUE,
    status           session_status NOT NULL,
    started_at       timestamptz    NOT NULL DEFAULT now(),
    last_activity_at timestamptz    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_conv_flow ON conversation_session (flow_id);
CREATE INDEX IF NOT EXISTS idx_conv_status ON conversation_session (status);

CREATE TABLE IF NOT EXISTS pipeline_generation_run
(
    id               uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    status           run_status  NOT NULL DEFAULT 'PENDING',
    flow_id          uuid        NULL REFERENCES flow (id) ON DELETE SET NULL,
    pipeline_id      uuid        NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    thread_id        text        NULL,
    started_at       timestamptz NOT NULL DEFAULT now(),
    finished_at      timestamptz NULL,
    duration_ms      int GENERATED ALWAYS AS (COALESCE((EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000)::int,
                                                       0)) STORED,
    usage            jsonb       NULL,
    error_code       text        NULL,
    error_message    text        NULL,
    created_by       text        NULL,
    prompt_hash      text        NULL,
    model            text        NULL,
    schema_version   text        NULL,
    input_params     jsonb       NULL,
    output_artifacts jsonb       NULL
);
CREATE INDEX IF NOT EXISTS idx_gen_run_main ON pipeline_generation_run (status, started_at);
CREATE INDEX IF NOT EXISTS idx_gen_run_flow ON pipeline_generation_run (flow_id);
CREATE INDEX IF NOT EXISTS idx_gen_run_pipeline ON pipeline_generation_run (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_gen_run_thread ON pipeline_generation_run (thread_id);

CREATE TABLE IF NOT EXISTS pipeline_upgrade_run
(
    id               uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    status           run_status  NOT NULL DEFAULT 'PENDING',
    flow_id          uuid        NULL REFERENCES flow (id) ON DELETE SET NULL,
    pipeline_id      uuid        NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    thread_id        text        NULL,
    started_at       timestamptz NOT NULL DEFAULT now(),
    finished_at      timestamptz NULL,
    duration_ms      int GENERATED ALWAYS AS (COALESCE((EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000)::int,
                                                       0)) STORED,
    usage            jsonb       NULL,
    error_code       text        NULL,
    error_message    text        NULL,
    created_by       text        NULL,
    from_pipeline_id uuid        NOT NULL REFERENCES pipeline (id) ON DELETE CASCADE,
    to_pipeline_id   uuid        NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    ruleset_id       text        NULL,
    diff_summary     jsonb       NULL,
    compat_score     numeric     NULL
);
CREATE INDEX IF NOT EXISTS idx_upg_run_main ON pipeline_upgrade_run (status, started_at);
CREATE INDEX IF NOT EXISTS idx_upg_run_flow ON pipeline_upgrade_run (flow_id);
CREATE INDEX IF NOT EXISTS idx_upg_run_pipeline ON pipeline_upgrade_run (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_upg_run_thread ON pipeline_upgrade_run (thread_id);
CREATE INDEX IF NOT EXISTS idx_upg_run_from ON pipeline_upgrade_run (from_pipeline_id);
CREATE INDEX IF NOT EXISTS idx_upg_run_to ON pipeline_upgrade_run (to_pipeline_id);

CREATE TABLE IF NOT EXISTS summary_run
(
    id            uuid PRIMARY KEY       DEFAULT gen_random_uuid(),
    status        run_status    NOT NULL DEFAULT 'PENDING',
    flow_id       uuid          NULL REFERENCES flow (id) ON DELETE SET NULL,
    pipeline_id   uuid          NULL REFERENCES pipeline (id) ON DELETE SET NULL,
    thread_id     text          NULL,
    started_at    timestamptz   NOT NULL DEFAULT now(),
    finished_at   timestamptz   NULL,
    duration_ms   int GENERATED ALWAYS AS (COALESCE((EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000)::int,
                                                    0)) STORED,
    usage         jsonb         NULL,
    error_code    text          NULL,
    error_message text          NULL,
    created_by    text          NULL,
    scope         summary_scope NOT NULL,
    target_id     text          NOT NULL,
    summary_id    uuid          NULL,
    strategy      text          NULL,
    notes         jsonb         NULL
);
CREATE INDEX IF NOT EXISTS idx_summary_run_main ON summary_run (status, started_at);
CREATE INDEX IF NOT EXISTS idx_summary_run_flow ON summary_run (flow_id);
CREATE INDEX IF NOT EXISTS idx_summary_run_pipeline ON summary_run (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_summary_run_thread ON summary_run (thread_id);
CREATE INDEX IF NOT EXISTS idx_summary_run_target ON summary_run (scope, target_id);

CREATE OR REPLACE VIEW flow_active_pipeline AS
SELECT p.*
FROM pipeline p
WHERE p.status = 'ACTIVE';

CREATE OR REPLACE VIEW job_run_all AS
SELECT 'GENERATION'::text as type,
       id,
       status,
       flow_id,
       pipeline_id,
       thread_id,
       started_at,
       finished_at,
       duration_ms,
       usage,
       error_code,
       error_message,
       created_by
FROM pipeline_generation_run
UNION ALL
SELECT 'UPGRADE'::text,
       id,
       status,
       flow_id,
       pipeline_id,
       thread_id,
       started_at,
       finished_at,
       duration_ms,
       usage,
       error_code,
       error_message,
       created_by
FROM pipeline_upgrade_run
UNION ALL
SELECT 'SUMMARY'::text,
       id,
       status,
       flow_id,
       pipeline_id,
       thread_id,
       started_at,
       finished_at,
       duration_ms,
       usage,
       error_code,
       error_message,
       created_by
FROM summary_run;