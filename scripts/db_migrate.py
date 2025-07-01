#!/usr/bin/env python
"""JobOps DB migration helper.

This standalone script performs idempotent schema migrations for the
`documents` table used by JobOps.

Key tasks (all optional / safe to re-run):
1. Create the `documents` table if it doesn't exist.
2. Drop legacy columns (`json_content`, `job_data_json`, `filename`).
3. Ensure `group_id` and `embedding` columns exist.
4. Switch journal mode to WAL for safer concurrent access.
5. VACUUM the database at the end to reclaim space.

Usage (from project root):

    python scripts/db_migrate.py  # uses default ~/.jobops/jobops.db
    python scripts/db_migrate.py /custom/path/jobops.db

The script is **non-destructive** for supported SQLite versions (>=3.35.0).
If your SQLite version is older and lacks `ALTER TABLE … DROP COLUMN`, the
script will skip the drop operations and continue.
"""
from __future__ import annotations

import sys
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

LEGACY_COLUMNS = ("json_content", "job_data_json", "filename")
REQUIRED_COLUMNS = {
    "group_id": "TEXT",
    "embedding": "BLOB",
}


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Return True if *column* exists in *table*."""
    cursor.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cursor.fetchall())


def create_documents_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            raw_content TEXT,
            structured_content TEXT,
            uploaded_at TEXT,
            group_id TEXT,
            embedding BLOB
        )
        """
    )


def migrate(db_path: Path) -> None:
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Using database: %s", db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")

        # 1. Ensure table exists
        create_documents_table(cur)

        # 2. Drop legacy columns (best-effort)
        for col in LEGACY_COLUMNS:
            try:
                if column_exists(cur, "documents", col):
                    logging.info("Dropping legacy column: %s", col)
                    cur.execute(f"ALTER TABLE documents DROP COLUMN {col}")
            except sqlite3.OperationalError:
                # SQLite <3.35 doesn't support DROP COLUMN – skip gracefully
                logging.warning("Skipping DROP COLUMN for %s (unsupported by SQLite version)", col)

        # 3. Add required columns
        for col, col_type in REQUIRED_COLUMNS.items():
            if not column_exists(cur, "documents", col):
                logging.info("Adding missing column: %s", col)
                cur.execute(f"ALTER TABLE documents ADD COLUMN {col} {col_type}")

        conn.commit()
        cur.execute("VACUUM;")
    logging.info("Migration completed successfully ✅")


if __name__ == "__main__":
    default_db = Path.home() / ".jobops" / "jobops.db"
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else default_db
    migrate(target) 