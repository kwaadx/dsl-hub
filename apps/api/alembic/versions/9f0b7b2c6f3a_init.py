from __future__ import annotations

from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f0b7b2c6f3a"
down_revision = None
branch_labels = None
depends_on = None

# Persisted slug matching the SQL filenames
slug = "init"


def _read_sql(kind: str) -> str:
    base_dir = Path(__file__).resolve().parent
    # primary file name includes the message slug
    path_with_slug = base_dir / "sql" / f"{revision}_{slug}_{kind}.sql"
    if path_with_slug.exists():
        return path_with_slug.read_text(encoding="utf-8")
    # fallback to files without slug, e.g., {revision}_upgrade.sql
    path_simple = base_dir / "sql" / f"{revision}_{kind}.sql"
    if path_simple.exists():
        return path_simple.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Expected SQL file not found. Looked for: {path_with_slug.name} or {path_simple.name} in 'versions/sql'."
    )


def upgrade() -> None:
    op.execute(_read_sql("upgrade"))


def downgrade() -> None:
    op.execute(_read_sql("downgrade"))
