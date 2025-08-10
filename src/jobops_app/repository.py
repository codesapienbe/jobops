from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Repository:
    db_path: str

    def __post_init__(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS job_applications (
                id TEXT PRIMARY KEY,
                canonical_url TEXT UNIQUE NOT NULL,
                job_title TEXT,
                company_name TEXT,
                application_date TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS section_data (
                id TEXT PRIMARY KEY,
                job_application_id TEXT NOT NULL,
                section_name TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(job_application_id, section_name),
                FOREIGN KEY(job_application_id) REFERENCES job_applications(id) ON DELETE CASCADE
            );
            """
        )
        self._conn.commit()

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def _gen_id(self, prefix: str) -> str:
        return f"{prefix}_{int(datetime.utcnow().timestamp()*1000)}"

    def canonicalize_url(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            p = urlparse(url)
            return f"{p.scheme}://{p.netloc}{p.path}"
        except Exception:
            return url

    def get_or_create_job(self, url: str, job_title: Optional[str] = None, company_name: Optional[str] = None) -> str:
        canonical = self.canonicalize_url(url)
        cur = self._conn.cursor()
        row = cur.execute("SELECT id FROM job_applications WHERE canonical_url=?", (canonical,)).fetchone()
        if row:
            return row[0]
        job_id = self._gen_id("job")
        now = self._now()
        cur.execute(
            """
            INSERT INTO job_applications (id, canonical_url, job_title, company_name, application_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, canonical, job_title, company_name, now[:10], "draft", now, now),
        )
        self._conn.commit()
        return job_id

    def upsert_section(self, job_application_id: str, section_name: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        now = self._now()
        cur = self._conn.cursor()
        # Try update first
        cur.execute(
            """
            UPDATE section_data SET data=?, updated_at=?
            WHERE job_application_id=? AND section_name=?
            """,
            (payload, now, job_application_id, section_name),
        )
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO section_data (id, job_application_id, section_name, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (self._gen_id("sec"), job_application_id, section_name, payload, now, now),
            )
        self._conn.commit()

    def get_section(self, job_application_id: str, section_name: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT data FROM section_data WHERE job_application_id=? AND section_name=?",
            (job_application_id, section_name),
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def get_job_meta(self, job_application_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT id, canonical_url, job_title, company_name, application_date, status, created_at, updated_at FROM job_applications WHERE id=?",
            (job_application_id,),
        ).fetchone()
        if not row:
            return None
        keys = ["id", "canonical_url", "job_title", "company_name", "application_date", "status", "created_at", "updated_at"]
        return {k: row[i] for i, k in enumerate(keys)}

    def list_jobs(self) -> List[Tuple[str, str]]:
        cur = self._conn.cursor()
        return [(r[0], r[1]) for r in cur.execute("SELECT id, canonical_url FROM job_applications ORDER BY updated_at DESC").fetchall()]

    def get_latest_job_id(self) -> Optional[str]:
        cur = self._conn.cursor()
        row = cur.execute("SELECT id FROM job_applications ORDER BY updated_at DESC LIMIT 1").fetchone()
        return row[0] if row else None

    def list_sections_for_job(self, job_application_id: str) -> Dict[str, Any]:
        cur = self._conn.cursor()
        rows = cur.execute(
            "SELECT section_name, data FROM section_data WHERE job_application_id=?",
            (job_application_id,),
        ).fetchall()
        out: Dict[str, Any] = {}
        for name, data in rows:
            try:
                out[name] = json.loads(data)
            except Exception:
                out[name] = {}
        return out

    def save_application_summary(self, job_application_id: str, summary_md: str) -> None:
        self.upsert_section(job_application_id, "application_summary", {"summary": summary_md})
