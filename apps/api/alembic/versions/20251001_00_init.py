from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251001_00_init"
down_revision = "b01d1001e001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = '''
-- =========================================================
-- DSL-Hub Authoring DB Schema (MVP+)
-- PostgreSQL 17+
-- =========================================================

-- ---------- Extensions ----------
create extension if not exists pgcrypto; -- gen_random_uuid()
create extension if not exists pg_trgm; -- trigram indexes
create extension if not exists citext;
-- case-insensitive text

-- ---------- Helper functions (no table dependencies) ----------
do
$$
    begin
        if not exists (select 1 from pg_proc where proname = 'set_updated_at') then
            create or replace function set_updated_at() returns trigger as
            $f$
            begin
                new.updated_at := now();
                return new;
            end
            $f$ language plpgsql;
        end if;

        if not exists (select 1 from pg_proc where proname = 'set_archived_ts') then
            create or replace function set_archived_ts() returns trigger as
            $fa$
            begin
                if new.archived and (old.archived is distinct from new.archived) then
                    new.archived_at := coalesce(new.archived_at, now());
                elsif not new.archived then
                    new.archived_at := null;
                end if;
                return new;
            end
            $fa$ language plpgsql;
        end if;
    end
$$;

-- =========================================================
-- 1) Flow / Thread / Message
-- =========================================================

create table if not exists flow
(
    id         uuid primary key     default gen_random_uuid(),
    slug       citext      not null unique,
    name       text        not null,
    meta       jsonb       not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
drop trigger if exists flow_set_updated_at on flow;
create trigger flow_set_updated_at
    before update
    on flow
    for each row
execute function set_updated_at();

create table if not exists thread
(
    id                  uuid primary key     default gen_random_uuid(),
    flow_id             uuid        not null references flow (id) on delete cascade,
    status              text        not null default 'NEW', -- NEW|IN_PROGRESS|SUCCESS|FAILED|ARCHIVED
    result_pipeline_id  uuid,                               -- FK added after pipeline
    context_snapshot_id uuid,                               -- FK added after context_snapshot
    archived            boolean     not null default false,
    archived_at         timestamptz,
    started_at          timestamptz not null default now(),
    closed_at           timestamptz,
    updated_at          timestamptz not null default now(),
    constraint thread_status_ck check (status in ('NEW', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'ARCHIVED')),
    constraint thread_ts_order_ck check (closed_at is null or closed_at >= started_at),
    constraint thread_archived_status_ck check (case when status = 'ARCHIVED' then archived else true end)
);
drop trigger if exists thread_set_updated_at on thread;
create trigger thread_set_updated_at
    before update
    on thread
    for each row
execute function set_updated_at();
drop trigger if exists thread_set_archived_ts on thread;
create trigger thread_set_archived_ts
    before update
    on thread
    for each row
execute function set_archived_ts();

create index if not exists thread_flow_status_started_idx
    on thread (flow_id, status, started_at desc);
create index if not exists thread_result_pipeline_idx
    on thread (result_pipeline_id);

create table if not exists message
(
    id          uuid primary key     default gen_random_uuid(),
    thread_id   uuid        not null references thread (id) on delete cascade,
    role        text        not null,                -- user|assistant|system|tool
    format      text        not null default 'text', -- text|markdown|json|buttons|card
    parent_id   uuid        references message (id) on delete set null,
    tool_name   text,
    tool_result jsonb,
    content     jsonb       not null,
    created_at  timestamptz not null default now(),
    constraint message_role_ck check (role in ('user', 'assistant', 'system', 'tool')),
    constraint message_format_ck check (format in ('text', 'markdown', 'json', 'buttons', 'card')),
    constraint message_content_type_ck check (jsonb_typeof(content) in ('object', 'array')),
    constraint message_tool_name_ck check (case when role = 'tool' then tool_name is not null else true end)
);
create index if not exists message_thread_created_idx on message (thread_id, created_at);
create index if not exists message_content_gin on message using gin (content jsonb_path_ops);
create index if not exists message_parent_idx on message (parent_id);

-- =========================================================
-- 2) Schema Definitions + Channels
-- =========================================================

create table if not exists schema_def
(
    id          uuid primary key     default gen_random_uuid(),
    name        text        not null,
    version     text        not null,                  -- semver X.Y.Z
    status      text        not null default 'active', -- active|deprecated
    json        jsonb       not null,
    compat_with text[]      not null default '{}',
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    constraint schema_def_name_version_uk unique (name, version),
    constraint schema_def_version_semver_ck check (version ~ '^\d+\.\d+\.\d+$'),
    constraint schema_def_status_ck check (status in ('active', 'deprecated'))
);
drop trigger if exists schema_def_set_updated_at on schema_def;
create trigger schema_def_set_updated_at
    before update
    on schema_def
    for each row
execute function set_updated_at();

create table if not exists schema_channel
(
    id                   uuid primary key     default gen_random_uuid(),
    name                 text        not null unique, -- e.g. 'stable'|'beta'|'next'
    active_schema_def_id uuid        not null references schema_def (id) on delete restrict,
    updated_at           timestamptz not null default now(),
    constraint schema_channel_name_ck check (name in ('stable', 'beta', 'next'))
);
drop trigger if exists schema_channel_set_updated_at on schema_channel;
create trigger schema_channel_set_updated_at
    before update
    on schema_channel
    for each row
execute function set_updated_at();

create index if not exists schema_channel_active_schema_idx
    on schema_channel (active_schema_def_id);

-- =========================================================
-- 3) Pipelines
-- =========================================================

create table if not exists pipeline
(
    id             uuid primary key     default gen_random_uuid(),
    flow_id        uuid        not null references flow (id) on delete cascade,
    version        text        not null,                 -- semver (config version)
    schema_version text        not null,                 -- semver (denormalized from schema_def)
    schema_def_id  uuid        not null references schema_def (id) on delete restrict,
    status         text        not null default 'draft', -- draft|review|published|archived
    is_published   boolean     not null default false,   -- single active per flow
    content        jsonb       not null,
    content_hash   bytea,                                -- expected 32 bytes (SHA-256)
    content_text   text generated always as (content::text) stored,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint pipeline_flow_version_uk unique (flow_id, version),
    constraint pipeline_version_semver_ck check (version ~ '^\d+\.\d+\.\d+$'),
    constraint pipeline_schema_version_semver_ck check (schema_version ~ '^\d+\.\d+\.\d+$'),
    constraint pipeline_status_ck check (status in ('draft', 'review', 'published', 'archived')),
    constraint pipeline_content_obj_ck check (jsonb_typeof(content) = 'object'),
    constraint pipeline_published_status_ck check (case when is_published then status = 'published' else true end),
    constraint pipeline_status_published_ck check (case when status = 'published' then is_published end),
    constraint pipeline_content_hash_len_ck check (content_hash is null or octet_length(content_hash) = 32)
);
create unique index if not exists pipeline_one_published_per_flow
    on pipeline (flow_id) where is_published = true;
create index if not exists pipeline_flow_idx on pipeline (flow_id);
create index if not exists pipeline_created_idx on pipeline (created_at);
create index if not exists pipeline_schema_def_idx on pipeline (schema_def_id);
create index if not exists pipeline_content_gin on pipeline using gin (content jsonb_path_ops);
create index if not exists pipeline_content_text_trgm
    on pipeline using gin (content_text gin_trgm_ops);
create unique index if not exists pipeline_flow_content_hash_uk
    on pipeline (flow_id, content_hash)
    where content_hash is not null;

drop trigger if exists pipeline_set_updated_at on pipeline;
create trigger pipeline_set_updated_at
    before update
    on pipeline
    for each row
execute function set_updated_at();

create or replace function pipeline_sync_schema_version() returns trigger as
$$
begin
    if new.schema_def_id is not null then
        select version into strict new.schema_version from schema_def where id = new.schema_def_id;
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists pipeline_sync_schema_version_trg on pipeline;
create trigger pipeline_sync_schema_version_trg
    before insert or update of schema_def_id
    on pipeline
    for each row
execute function pipeline_sync_schema_version();

alter table thread
    drop constraint if exists thread_result_pipeline_fkey;
alter table thread
    add constraint thread_result_pipeline_fkey
        foreign key (result_pipeline_id) references pipeline (id) on delete set null;

-- =========================================================
-- 4) Generation Runs + Validation Issues
-- =========================================================

create table if not exists generation_run
(
    id          uuid primary key     default gen_random_uuid(),
    flow_id     uuid        not null references flow (id) on delete cascade,
    thread_id   uuid        references thread (id) on delete set null,
    pipeline_id uuid        references pipeline (id) on delete set null,
    stage       text        not null,                  -- discovery|generate|self_check|hard_validate|publish
    status      text        not null default 'queued', -- queued|running|succeeded|failed|canceled
    source      jsonb       not null,
    result      jsonb,
    error       text,
    cost        jsonb,
    created_at  timestamptz not null default now(),
    started_at  timestamptz,
    finished_at timestamptz,
    constraint generation_run_status_ck check (status in ('queued', 'running', 'succeeded', 'failed', 'canceled')),
    constraint generation_run_stage_ck check (stage in
                                              ('discovery', 'generate', 'self_check', 'hard_validate', 'publish')),
    constraint generation_run_ts_order_ck check (
        (started_at is null or started_at >= created_at) and
        (finished_at is null or (started_at is not null and finished_at >= started_at))
        ),
    constraint generation_run_source_obj_ck check (jsonb_typeof(source) = 'object'),
    constraint generation_run_result_obj_ck check (result is null or jsonb_typeof(result) = 'object'),
    constraint generation_run_cost_obj_ck check (cost is null or jsonb_typeof(cost) = 'object')
);
create index if not exists generation_run_flow_status_idx
    on generation_run (flow_id, status, created_at desc);
create index if not exists generation_run_thread_idx
    on generation_run (thread_id, created_at desc);
create index if not exists generation_run_pipeline_idx
    on generation_run (pipeline_id, created_at desc);

create table if not exists validation_issue
(
    id                uuid primary key     default gen_random_uuid(),
    generation_run_id uuid        not null references generation_run (id) on delete cascade,
    path              text        not null,
    code              text        not null,
    severity          text        not null, -- info|warning|error
    message           text        not null,
    created_at        timestamptz not null default now(),
    constraint validation_issue_severity_ck check (severity in ('info', 'warning', 'error'))
);
create index if not exists validation_issue_run_idx
    on validation_issue (generation_run_id);

-- =========================================================
-- 5) Agent Log
-- =========================================================

create table if not exists agent_log
(
    id         uuid primary key     default gen_random_uuid(),
    flow_id    uuid        references flow (id) on delete set null,
    thread_id  uuid        references thread (id) on delete set null,
    level      text        not null, -- debug|info|warn|error
    event      text        not null,
    data       jsonb,
    created_at timestamptz not null default now(),
    constraint agent_log_level_ck check (level in ('debug', 'info', 'warn', 'error'))
);
create index if not exists agent_log_created_idx on agent_log (created_at);
create index if not exists agent_log_flow_idx on agent_log (flow_id);
create index if not exists agent_log_thread_idx on agent_log (thread_id);

-- =========================================================
-- 6) Summaries
-- =========================================================

create table if not exists flow_summary
(
    id              uuid primary key     default gen_random_uuid(),
    flow_id         uuid        not null references flow (id) on delete cascade,
    version         int         not null default 1,
    content         jsonb       not null,
    pinned          jsonb       not null default '{}'::jsonb,
    last_message_id uuid,
    is_active       boolean     not null default false,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    constraint flow_summary_flow_version_uk unique (flow_id, version),
    constraint flow_summary_content_obj_ck check (jsonb_typeof(content) = 'object'),
    constraint flow_summary_pinned_obj_ck check (jsonb_typeof(pinned) = 'object'),
    constraint flow_summary_version_pos_ck check (version >= 1)
);
alter table flow_summary
    drop constraint if exists flow_summary_last_msg_fk;
alter table flow_summary
    add constraint flow_summary_last_msg_fk
        foreign key (last_message_id) references message (id) on delete set null;

create unique index if not exists flow_summary_one_active_per_flow
    on flow_summary (flow_id) where is_active = true;
create index if not exists flow_summary_content_gin
    on flow_summary using gin (content jsonb_path_ops);

drop trigger if exists flow_summary_set_updated_at on flow_summary;
create trigger flow_summary_set_updated_at
    before update
    on flow_summary
    for each row
execute function set_updated_at();

alter table flow_summary
    add column if not exists content_text text generated always as (content::text) stored;
create index if not exists flow_summary_content_text_trgm
    on flow_summary using gin (content_text gin_trgm_ops);

create table if not exists thread_summary
(
    id            uuid primary key     default gen_random_uuid(),
    thread_id     uuid        not null references thread (id) on delete cascade,
    kind          text        not null default 'short', -- short|detailed|system
    content       jsonb       not null,
    token_budget  int         not null default 1024,
    covering_from timestamptz,
    covering_to   timestamptz,
    created_at    timestamptz not null default now(),
    constraint thread_summary_kind_ck check (kind in ('short', 'detailed', 'system')),
    constraint thread_summary_content_obj_ck check (jsonb_typeof(content) = 'object'),
    constraint thread_summary_covering_order_ck
        check (covering_to is null or covering_from is null or covering_to >= covering_from)
);
create index if not exists thread_summary_thread_idx on thread_summary (thread_id);
create index if not exists thread_summary_content_gin
    on thread_summary using gin (content jsonb_path_ops);

alter table thread_summary
    add column if not exists content_text text generated always as (content::text) stored;
create index if not exists thread_summary_content_text_trgm
    on thread_summary using gin (content_text gin_trgm_ops);

-- =========================================================
-- 7) Context Snapshot
-- =========================================================

create table if not exists context_snapshot
(
    id               uuid primary key     default gen_random_uuid(),
    flow_id          uuid        not null references flow (id) on delete cascade,
    origin_thread_id uuid        references thread (id) on delete set null,
    schema_def_id    uuid        not null references schema_def (id) on delete restrict,
    flow_summary_id  uuid        references flow_summary (id) on delete set null,
    pipeline_id      uuid        references pipeline (id) on delete set null,
    notes            jsonb       not null default '{}'::jsonb,
    created_at       timestamptz not null default now(),
    constraint context_snapshot_notes_obj_ck check (jsonb_typeof(notes) = 'object')
);
create index if not exists context_snapshot_flow_created_idx
    on context_snapshot (flow_id, created_at desc);
create index if not exists context_snapshot_origin_thread_idx
    on context_snapshot (origin_thread_id);

alter table thread
    drop constraint if exists thread_context_snapshot_fkey;
alter table thread
    add constraint thread_context_snapshot_fkey
        foreign key (context_snapshot_id) references context_snapshot (id) on delete set null;

-- =========================================================
-- 8) Summary Runs
-- =========================================================

create table if not exists summary_run
(
    id              uuid primary key     default gen_random_uuid(),
    flow_id         uuid        not null references flow (id) on delete cascade,
    thread_id       uuid        references thread (id) on delete set null,
    flow_summary_id uuid        references flow_summary (id) on delete set null,
    stage           text        not null,                  -- collect|chunk|summarize|merge|commit
    status          text        not null default 'queued', -- queued|running|succeeded|failed
    source          jsonb       not null,
    result          jsonb,
    error           text,
    cost            jsonb,
    created_at      timestamptz not null default now(),
    started_at      timestamptz,
    finished_at     timestamptz,
    constraint summary_run_status_ck check (status in ('queued', 'running', 'succeeded', 'failed')),
    constraint summary_run_stage_ck check (stage in ('collect', 'chunk', 'summarize', 'merge', 'commit')),
    constraint summary_run_ts_order_ck check (
        (started_at is null or started_at >= created_at) and
        (finished_at is null or (started_at is not null and finished_at >= started_at))
        ),
    constraint summary_run_source_obj_ck check (jsonb_typeof(source) = 'object'),
    constraint summary_run_result_obj_ck check (result is null or jsonb_typeof(result) = 'object'),
    constraint summary_run_cost_obj_ck check (cost is null or jsonb_typeof(cost) = 'object')
);
create index if not exists summary_run_flow_status_idx
    on summary_run (flow_id, status, created_at desc);
create index if not exists summary_run_thread_idx
    on summary_run (thread_id, created_at desc);
create index if not exists summary_run_flow_summary_idx
    on summary_run (flow_summary_id, created_at desc);

-- =========================================================
-- 9) Prompt Templates
-- =========================================================

create table if not exists prompt_template
(
    key        text primary key, -- e.g. 'generate'|'self_check'|'hard_validate'|'summarize'|'migrate'
    text       text        not null,
    meta       jsonb       not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);
drop trigger if exists prompt_template_set_updated_at on prompt_template;
create trigger prompt_template_set_updated_at
    before update
    on prompt_template
    for each row
execute function set_updated_at();

-- =========================================================
-- 10) Schema Upgrades
-- =========================================================

create table if not exists schema_upgrade_plan
(
    id                 uuid primary key     default gen_random_uuid(),
    name               text        not null,
    from_schema_def_id uuid        not null references schema_def (id) on delete restrict,
    to_schema_def_id   uuid        not null references schema_def (id) on delete restrict,
    strategy           text        not null default 'transform', -- transform|no_change|manual_only|deprecated
    transform_spec     jsonb       not null default '{}'::jsonb,
    notes              text,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now(),
    constraint schema_upgrade_plan_from_to_uk unique (from_schema_def_id, to_schema_def_id),
    constraint schema_upgrade_plan_strategy_ck check (strategy in ('transform', 'no_change', 'manual_only', 'deprecated')),
    constraint schema_upgrade_plan_from_to_diff_ck check (from_schema_def_id <> to_schema_def_id)
);
drop trigger if exists schema_upgrade_plan_set_updated_at on schema_upgrade_plan;
create trigger schema_upgrade_plan_set_updated_at
    before update
    on schema_upgrade_plan
    for each row
execute function set_updated_at();

create table if not exists pipeline_upgrade_run
(
    id                 uuid primary key     default gen_random_uuid(),
    pipeline_id        uuid        not null references pipeline (id) on delete cascade,
    from_schema_def_id uuid        not null references schema_def (id) on delete restrict,
    to_schema_def_id   uuid        not null references schema_def (id) on delete restrict,
    upgrade_plan_id    uuid        references schema_upgrade_plan (id) on delete set null,
    status             text        not null default 'queued', -- queued|running|succeeded|failed|skipped
    mode               text        not null default 'auto',   -- auto|assisted|manual
    diff               jsonb,
    issues             jsonb,
    created_at         timestamptz not null default now(),
    started_at         timestamptz,
    finished_at        timestamptz,
    constraint pipeline_upgrade_run_status_ck check (status in ('queued', 'running', 'succeeded', 'failed', 'skipped')),
    constraint pipeline_upgrade_run_mode_ck check (mode in ('auto', 'assisted', 'manual')),
    constraint pipeline_upgrade_run_ts_order_ck check (
        (started_at is null or started_at >= created_at) and
        (finished_at is null or (started_at is not null and finished_at >= started_at))
        ),
    constraint pipeline_upgrade_run_diff_obj_ck check (diff is null or jsonb_typeof(diff) = 'object'),
    constraint pipeline_upgrade_run_issues_obj_ck check (issues is null or jsonb_typeof(issues) = 'object')
);
create index if not exists pipeline_upgrade_run_pipeline_idx
    on pipeline_upgrade_run (pipeline_id, created_at desc);

create table if not exists compat_rule
(
    id              uuid primary key     default gen_random_uuid(),
    schema_def_id   uuid        not null references schema_def (id) on delete cascade,
    compatible_with text[]      not null default '{}',
    notes           text,
    updated_at      timestamptz not null default now()
);
create index if not exists compat_rule_schema_idx on compat_rule (schema_def_id);
drop trigger if exists compat_rule_set_updated_at on compat_rule;
create trigger compat_rule_set_updated_at
    before update
    on compat_rule
    for each row
execute function set_updated_at();

-- =========================================================
-- Cross-flow integrity functions/triggers (defined after tables)
-- =========================================================

-- Parent message must be in the same thread
create or replace function message_parent_same_thread() returns trigger as
$$
declare
    parent_thread uuid;
begin
    if new.parent_id is not null then
        select thread_id into parent_thread from message where id = new.parent_id;
        if parent_thread is null or parent_thread <> new.thread_id then
            raise exception 'parent message must belong to the same thread';
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists message_parent_same_thread_trg on message;
create trigger message_parent_same_thread_trg
    before insert or update
    on message
    for each row
execute function message_parent_same_thread();

-- flow_summary.last_message_id must belong to the same flow
create or replace function flow_summary_last_msg_same_flow() returns trigger as
$$
declare
    m_thread uuid; m_flow uuid;
begin
    if new.last_message_id is null then
        return new;
    end if;
    select thread_id into m_thread from message where id = new.last_message_id;
    if m_thread is null then
        return new;
    end if;
    select flow_id into m_flow from thread where id = m_thread;
    if m_flow is null or m_flow <> new.flow_id then
        raise exception 'last_message_id must belong to the same flow';
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists flow_summary_last_msg_same_flow_trg on flow_summary;
create trigger flow_summary_last_msg_same_flow_trg
    before insert or update of last_message_id, flow_id
    on flow_summary
    for each row
execute function flow_summary_last_msg_same_flow();

-- context_snapshot.pipeline_id / flow_summary_id must belong to the same flow
create or replace function context_snapshot_same_flow() returns trigger as
$$
declare
    p_flow uuid; fs_flow uuid;
begin
    if new.pipeline_id is not null then
        select flow_id into p_flow from pipeline where id = new.pipeline_id;
        if p_flow is null or p_flow <> new.flow_id then
            raise exception 'pipeline_id must belong to the same flow';
        end if;
    end if;

    if new.flow_summary_id is not null then
        select flow_id into fs_flow from flow_summary where id = new.flow_summary_id;
        if fs_flow is null or fs_flow <> new.flow_id then
            raise exception 'flow_summary_id must belong to the same flow';
        end if;
    end if;

    return new;
end;
$$ language plpgsql;

drop trigger if exists context_snapshot_same_flow_trg on context_snapshot;
create trigger context_snapshot_same_flow_trg
    before insert or update of flow_id, pipeline_id, flow_summary_id
    on context_snapshot
    for each row
execute function context_snapshot_same_flow();

-- generation_run.thread_id / pipeline_id must match generation_run.flow_id
create or replace function generation_run_same_flow() returns trigger as
$$
declare
    t_flow uuid; p_flow uuid;
begin
    if new.thread_id is not null then
        select flow_id into t_flow from thread where id = new.thread_id;
        if t_flow is null or t_flow <> new.flow_id then
            raise exception 'thread_id must belong to the same flow (generation_run.flow_id)';
        end if;
    end if;

    if new.pipeline_id is not null then
        select flow_id into p_flow from pipeline where id = new.pipeline_id;
        if p_flow is null or p_flow <> new.flow_id then
            raise exception 'pipeline_id must belong to the same flow (generation_run.flow_id)';
        end if;
    end if;

    return new;
end;
$$ language plpgsql;

drop trigger if exists generation_run_same_flow_trg on generation_run;
create trigger generation_run_same_flow_trg
    before insert or update of flow_id, thread_id, pipeline_id
    on generation_run
    for each row
execute function generation_run_same_flow();

-- summary_run.thread_id / flow_summary_id must match summary_run.flow_id
create or replace function summary_run_same_flow() returns trigger as
$$
declare
    t_flow uuid; fs_flow uuid;
begin
    if new.thread_id is not null then
        select flow_id into t_flow from thread where id = new.thread_id;
        if t_flow is null or t_flow <> new.flow_id then
            raise exception 'thread_id must belong to the same flow (summary_run.flow_id)';
        end if;
    end if;

    if new.flow_summary_id is not null then
        select flow_id into fs_flow from flow_summary where id = new.flow_summary_id;
        if fs_flow is null or fs_flow <> new.flow_id then
            raise exception 'flow_summary_id must belong to the same flow (summary_run.flow_id)';
        end if;
    end if;

    return new;
end;
$$ language plpgsql;

drop trigger if exists summary_run_same_flow_trg on summary_run;
create trigger summary_run_same_flow_trg
    before insert or update of flow_id, thread_id, flow_summary_id
    on summary_run
    for each row
execute function summary_run_same_flow();

-- thread.result_pipeline_id must match thread.flow_id
create or replace function thread_result_pipeline_same_flow() returns trigger as
$$
declare
    p_flow uuid;
begin
    if new.result_pipeline_id is not null then
        select flow_id into p_flow from pipeline where id = new.result_pipeline_id;
        if p_flow is null or p_flow <> new.flow_id then
            raise exception 'result_pipeline_id must belong to the same flow (thread.flow_id)';
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists thread_result_pipeline_same_flow_trg on thread;
create trigger thread_result_pipeline_same_flow_trg
    before insert or update of flow_id, result_pipeline_id
    on thread
    for each row
execute function thread_result_pipeline_same_flow();

-- thread.context_snapshot_id must match thread.flow_id
create or replace function thread_context_snapshot_same_flow() returns trigger as
$$
declare
    cs_flow uuid;
begin
    if new.context_snapshot_id is not null then
        select flow_id into cs_flow from context_snapshot where id = new.context_snapshot_id;
        if cs_flow is null or cs_flow <> new.flow_id then
            raise exception 'context_snapshot_id must belong to the same flow (thread.flow_id)';
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists thread_context_snapshot_same_flow_trg on thread;
create trigger thread_context_snapshot_same_flow_trg
    before insert or update of flow_id, context_snapshot_id
    on thread
    for each row
execute function thread_context_snapshot_same_flow();

-- =========================================================
-- Convenience view(s)
-- =========================================================

create or replace view flow_active_pipeline as
select *
from pipeline
where is_published = true;
'''
    op.execute(sql)


def downgrade() -> None:
    # Irreversible migration (schema bootstrap). No-op.
    pass
