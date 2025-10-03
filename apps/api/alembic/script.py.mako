"""Generic Alembic environment config."""
from alembic import context
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory


def run_lambda(migration_fn):
    """Utility wrapper for custom execution if ever needed."""
    config = context.config
    script = ScriptDirectory.from_config(config)
    def upgrade(rev, context):
        return migration_fn(rev, context)
    env = EnvironmentContext(config, script)
    with env:
        env.run_migrations_online = upgrade  # type: ignore[attr-defined]
        env.configure()
        env.run_migrations()
