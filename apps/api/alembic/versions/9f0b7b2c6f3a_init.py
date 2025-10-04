"""init

Revision ID: 2c344ed3fb38
Revises: a47e1e313db5
Create Date: 2025-10-04 12:50:01.247306
"""

from __future__ import annotations

from pathlib import Path
from alembic import op

revision = "9f0b7b2c6f3a"
down_revision = None
branch_labels = None
depends_on = None

slug = "init"


def _read_sql(kind: str) -> str:
    base_dir = Path(__file__).resolve().parent
    path_with_slug = base_dir / "sql" / f"{revision}_{slug}_{kind}.sql"
    if path_with_slug.exists():
        return path_with_slug.read_text(encoding="utf-8")
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
