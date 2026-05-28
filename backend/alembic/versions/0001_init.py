"""initial schema equivalent to infra/migrations/0001_init.sql

Revision ID: 0001_init
Revises:
Create Date: 2026-05-28 00:00:00

This revision applies the canonical schema. On PostgreSQL it loads the raw
SQL file directly so that TimescaleDB hypertables, ARRAY columns and INET
types are produced exactly as the DBA approved. On non-PG dialects (e.g.
SQLite in tests), it falls back to creating tables from the SQLAlchemy
metadata.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Locate the canonical SQL file relative to the backend dir (default) or
# inside the repo at ../infra/migrations/0001_init.sql when run in-tree.
def _find_init_sql() -> Path | None:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent.parent.parent / "infra" / "migrations" / "0001_init.sql",
        Path(os.environ.get("CT_INIT_SQL", "")).resolve()
        if os.environ.get("CT_INIT_SQL")
        else None,
    ]
    for p in candidates:
        if p and p.is_file():
            return p
    return None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        sql_file = _find_init_sql()
        if sql_file is None:
            raise RuntimeError(
                "Could not locate infra/migrations/0001_init.sql; set CT_INIT_SQL env."
            )
        sql = sql_file.read_text()
        for stmt in _split_statements(sql):
            op.execute(sa.text(stmt))
    else:
        # SQLite / others: rebuild from ORM metadata.
        from app.db.base import Base
        import app.db.models  # noqa: F401
        Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from app.db.base import Base
    import app.db.models  # noqa: F401
    Base.metadata.drop_all(bind=bind)


def _split_statements(sql: str) -> list[str]:
    """Naive SQL splitter (handles single statements terminated by ';')."""
    cleaned: list[str] = []
    buf: list[str] = []
    in_dollar = False
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        # crude dollar-quote tracking (not really used here)
        if "$$" in line:
            in_dollar = not in_dollar
        if ";" in line and not in_dollar:
            stmt = "\n".join(buf).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1].strip()
            if stmt:
                cleaned.append(stmt)
            buf = []
    if buf and "\n".join(buf).strip():
        cleaned.append("\n".join(buf).strip())
    return cleaned
