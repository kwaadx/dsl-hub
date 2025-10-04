"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from __future__ import annotations

from pathlib import Path
from alembic import op

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}
<%
import re

def make_slug(msg):
    if not msg:
        return "migration"
    slug = re.sub(r"\s+", "_", msg.strip().lower())
    slug = re.sub(r"[^a-z0-9_]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "migration"

safe_slug = make_slug(message)
%>
slug = ${repr(safe_slug)}


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
