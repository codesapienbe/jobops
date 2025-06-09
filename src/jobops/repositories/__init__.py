from datetime import datetime
import logging  
from pathlib import Path
from typing import Protocol, List, Optional
from jobops.models import Document, DocumentType
import sqlite3

class DocumentRepository(Protocol):
    def save(self, document: Document) -> str: ...
    def get_by_id(self, doc_id: str) -> Optional[Document]: ...
    def get_by_type(self, doc_type: DocumentType) -> List[Document]: ...
    def get_latest_resume(self) -> Optional[str]: ...
    def delete(self, doc_id: str) -> bool: ...

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
                    filename TEXT,
                    raw_content TEXT,
                    structured_content TEXT,
                    uploaded_at TEXT
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
            conn.commit()
    
    def save(self, document: Document) -> str:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT OR REPLACE INTO documents 
                   (id, type, filename, raw_content, structured_content, uploaded_at) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (document.id, document.type.value, document.filename,
                 document.raw_content, document.structured_content,
                 document.uploaded_at.isoformat())
            )
            conn.commit()
        return document.id
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = c.fetchone()
            
            if row:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    filename=row[2],
                    raw_content=row[3],
                    structured_content=row[4],
                    uploaded_at=datetime.fromisoformat(row[5])
                )
                return doc
        return None
    
    def get_by_type(self, doc_type: DocumentType) -> List[Document]:
        documents = []
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM documents WHERE type = ? ORDER BY uploaded_at DESC", 
                (doc_type.value,)
            )
            rows = c.fetchall()
            
            for row in rows:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    filename=row[2],
                    raw_content=row[3],
                    structured_content=row[4],
                    uploaded_at=datetime.fromisoformat(row[5])
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
