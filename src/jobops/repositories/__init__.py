from datetime import datetime
import logging  
from pathlib import Path
from typing import List, Optional
from jobops.models import Document, DocumentType, Solicitation, SolicitationReport
import sqlite3
import json

class SQLiteDocumentRepository:
    def __init__(self, db_path: str, timeout: float = 30.0):
        self.db_path = Path(db_path)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute('PRAGMA journal_mode=WAL;')
            c.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    raw_content TEXT,
                    structured_content TEXT,
                    uploaded_at TEXT,
                    group_id TEXT
                )
            ''')
            # Migration: drop json_content and job_data_json columns if they exist
            try:
                c.execute('ALTER TABLE documents DROP COLUMN json_content')
            except Exception:
                pass
            try:
                c.execute('ALTER TABLE documents DROP COLUMN job_data_json')
            except Exception:
                pass
            # Migration: drop filename column if present (for existing DBs)
            try:
                c.execute('ALTER TABLE documents DROP COLUMN filename')
            except Exception:
                pass
            # Migration: add group_id column if not exists
            try:
                c.execute('ALTER TABLE documents ADD COLUMN group_id TEXT')
            except Exception:
                pass
            conn.commit()
    
    def save(self, document: Document) -> Optional[str]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO documents 
                (id, type, raw_content, structured_content, uploaded_at, group_id) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.type.value,
                    document.raw_content,
                    document.structured_content,
                    document.uploaded_at.isoformat(),
                    document.group_id
                )
            )
            conn.commit()
        return document.id
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id, type, raw_content, structured_content, uploaded_at, group_id FROM documents WHERE id = ?", (doc_id,))
            row = c.fetchone()
            
            if row:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    raw_content=row[2],
                    structured_content=row[3],
                    uploaded_at=datetime.fromisoformat(row[4]),
                    group_id=row[5]
                )
                return doc
        return None
    
    def get_by_type(self, doc_type: DocumentType) -> List[Document]:
        documents = []
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, type, raw_content, structured_content, uploaded_at, group_id FROM documents WHERE type = ? ORDER BY uploaded_at DESC", 
                (doc_type.value,)
            )
            rows = c.fetchall()
            
            for row in rows:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    raw_content=row[2],
                    structured_content=row[3],
                    uploaded_at=datetime.fromisoformat(row[4]),
                    group_id=row[5]
                )
                documents.append(doc)
        return documents
    
    def get_latest_resume(self) -> Optional[str]:
        documents = self.get_by_type(DocumentType.RESUME)
        if documents:
            return documents[0].structured_content  # Markdown content
        return None
    
    def delete(self, doc_id: str) -> bool:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            deleted = c.rowcount > 0
            conn.commit()
        return deleted

    def get_by_group(self, group_id: str) -> List[Document]:
        """Retrieve documents belonging to a given group ID."""
        documents: List[Document] = []
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, type, raw_content, structured_content, uploaded_at, group_id FROM documents WHERE group_id = ? ORDER BY type", 
                (group_id,)
            )
            rows = c.fetchall()
            for row in rows:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    raw_content=row[2],
                    structured_content=row[3],
                    uploaded_at=datetime.fromisoformat(row[4]),
                    group_id=row[5]
                )
                documents.append(doc)
        return documents

    def list_group_ids(self) -> List[str]:
        """List distinct non-null group IDs."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT group_id FROM documents WHERE group_id IS NOT NULL")
            return [row[0] for row in c.fetchall()]

class SQLiteSolicitationRepository:
    def __init__(self, db_path: str, timeout: float = 30.0):
        self.db_path = Path(db_path)
        self.timeout = timeout
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            c.execute('''
                CREATE TABLE IF NOT EXISTS solicitation_reports (
                    id TEXT PRIMARY KEY,
                    periode TEXT NOT NULL,
                    totaal_sollicitaties INTEGER NOT NULL,
                    status_overzicht TEXT,
                    sollicitatie_platforms TEXT,
                    locatie_verdeling TEXT,
                    motivatiebrieven TEXT,
                    interviews_assessments TEXT,
                    networking TEXT,
                    documenten_gereed TEXT,
                    vdab_opdrachten TEXT,
                    opmerkingen TEXT,
                    generated_at TEXT NOT NULL
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS solicitations (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    datum TEXT,
                    bedrijf TEXT,
                    functie TEXT,
                    status TEXT,
                    resultaat TEXT,
                    locatie TEXT,
                    platform TEXT,
                    FOREIGN KEY(report_id) REFERENCES solicitation_reports(id) ON DELETE CASCADE
                )
            ''')
            conn.commit()

    def save_report(self, report: SolicitationReport) -> Optional[str]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT OR REPLACE INTO solicitation_reports
                   (id, periode, totaal_sollicitaties, status_overzicht, sollicitatie_platforms, locatie_verdeling,
                    motivatiebrieven, interviews_assessments, networking, documenten_gereed, vdab_opdrachten, opmerkingen, generated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (report.id, report.periode, report.totaal_sollicitaties,
                 json.dumps(report.status_overzicht), json.dumps(report.sollicitatie_platforms),
                 json.dumps(report.locatie_verdeling), json.dumps(report.motivatiebrieven),
                 json.dumps(report.interviews_assessments), json.dumps(report.networking),
                 json.dumps(report.documenten_gereed), json.dumps(report.vdab_opdrachten),
                 report.opmerkingen, report.generated_at.isoformat())
            )
            for sol in report.sollicitaties:
                c.execute(
                    """INSERT OR REPLACE INTO solicitations
                       (id, report_id, datum, bedrijf, functie, status, resultaat, locatie, platform)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sol.id, report.id, sol.datum, sol.bedrijf, sol.functie,
                     sol.status, sol.resultaat, sol.locatie, sol.platform)
                )
            conn.commit()
        return report.id

    def get_report_by_id(self, report_id: str) -> Optional[SolicitationReport]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id, periode, totaal_sollicitaties, status_overzicht, sollicitatie_platforms, locatie_verdeling, motivatiebrieven, interviews_assessments, networking, documenten_gereed, vdab_opdrachten, opmerkingen, generated_at FROM solicitation_reports WHERE id = ?", (report_id,))
            row = c.fetchone()
            if not row:
                return None
            report = SolicitationReport(
                id=row[0], periode=row[1], totaal_sollicitaties=row[2],
                status_overzicht=json.loads(row[3]), sollicitatie_platforms=json.loads(row[4]),
                locatie_verdeling=json.loads(row[5]), motivatiebrieven=json.loads(row[6]),
                interviews_assessments=json.loads(row[7]), networking=json.loads(row[8]),
                documenten_gereed=json.loads(row[9]), vdab_opdrachten=json.loads(row[10]),
                opmerkingen=row[11], generated_at=datetime.fromisoformat(row[12]), sollicitaties=[]
            )
            c.execute("SELECT id, report_id, datum, bedrijf, functie, status, resultaat, locatie, platform FROM solicitations WHERE report_id = ?", (report_id,))
            rows = c.fetchall()
            solicitations = []
            for r in rows:
                solicitations.append(Solicitation(
                    id=r[0], report_id=r[1], datum=r[2], bedrijf=r[3],
                    functie=r[4], status=r[5], resultaat=r[6], locatie=r[7], platform=r[8]
                ))
            report.sollicitaties = solicitations
            return report

    def get_latest_report(self) -> Optional[SolicitationReport]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM solicitation_reports ORDER BY generated_at DESC LIMIT 1")
            row = c.fetchone()
            if row:
                return self.get_report_by_id(row[0])
        return None

    def list_reports(self) -> List[Optional[SolicitationReport]]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM solicitation_reports ORDER BY generated_at DESC")
            rows = c.fetchall()
            return [self.get_report_by_id(r[0]) for r in rows if r]

    def save_solicitation(self, solicitation: Solicitation) -> Optional[str]:
        """Save a single solicitation record independently."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            # Create table if not exists
            c.execute('''
                CREATE TABLE IF NOT EXISTS solicitation_records (
                    id TEXT PRIMARY KEY,
                    datum TEXT,
                    bedrijf TEXT,
                    functie TEXT,
                    status TEXT,
                    resultaat TEXT,
                    locatie TEXT,
                    platform TEXT
                )
            ''')
            c.execute(
                "INSERT OR REPLACE INTO solicitation_records (id, datum, bedrijf, functie, status, resultaat, locatie, platform) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (solicitation.id, solicitation.datum, solicitation.bedrijf, solicitation.functie, solicitation.status, solicitation.resultaat, solicitation.locatie, solicitation.platform)
            )
            conn.commit()
        return solicitation.id

    def list_solicitations(self) -> List[Optional[Solicitation]]:
        """List all independent solicitation records."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id, datum, bedrijf, functie, status, resultaat, locatie, platform FROM solicitation_records ORDER BY ROWID DESC")
            rows = c.fetchall()
            records = []
            for r in rows:
                records.append(Solicitation(
                    id=r[0], datum=r[1], bedrijf=r[2], functie=r[3], status=r[4], resultaat=r[5], locatie=r[6], platform=r[7]
                ))
        return records

    def get_solicitation_by_id(self, record_id: str) -> Optional[Solicitation]:
        """Get a single solicitation record by ID."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT id, datum, bedrijf, functie, status, resultaat, locatie, platform FROM solicitation_records WHERE id = ?", (record_id,))
            r = c.fetchone()
            if not r:
                return None
            return Solicitation(id=r[0], datum=r[1], bedrijf=r[2], functie=r[3], status=r[4], resultaat=r[5], locatie=r[6], platform=r[7])
