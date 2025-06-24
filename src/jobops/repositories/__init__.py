from datetime import datetime
import logging  
from pathlib import Path
from typing import List, Optional
from jobops.models import Document, DocumentType
import sqlite3

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

