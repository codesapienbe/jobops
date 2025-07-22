from typing import List, Tuple, Any, Dict, Optional
import logging
from pathlib import Path
import os
import re
from rich.logging import RichHandler

# Ensure all loggers in this module use RichHandler for colored console output
root_logger = logging.getLogger()
if not any(isinstance(h, RichHandler) for h in root_logger.handlers):
    rich_handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True, show_path=False)
    rich_handler.setLevel(logging.INFO)
    root_logger.addHandler(rich_handler)

from ..models import Document, DocumentType
from ..repositories import SQLiteDocumentRepository
from ..config import CONSTANTS

from ..clients import embed_structured_data
import numpy as np
import joblib

logger = logging.getLogger(__name__)


def clean(documents: List[Document]) -> List[Document]:
    """Clean structured content of documents by normalizing text."""
    cleaned_docs: List[Document] = []
    for doc in documents:
        text = doc.structured_content or doc.raw_content
        # Basic cleaning: lowercase and collapse whitespace
        cleaned_text = " ".join(text.lower().split())
        doc.structured_content = cleaned_text
        cleaned_docs.append(doc)
    return cleaned_docs


def ingest(documents: List[Document], llm_client) -> Tuple[np.ndarray, List[Document]]:
    """Convert documents into embedding vectors and keep document references."""
    embeddings_list: List[List[float]] = []
    for doc in documents:
        content = doc.structured_content or doc.raw_content
        emb = llm_client.embed_structured_data(content)
        embeddings_list.append(emb)
    embeddings = np.array(embeddings_list)
    return embeddings, documents


def train(embeddings: np.ndarray) -> np.ndarray:
    """Pass through embeddings array for similarity lookup."""
    return embeddings


def predict(job_description: str, embeddings: np.ndarray, documents: List[Document], llm_client, top_k: int = 1) -> List[Document]:
    """Given a new job description, find the top_k most similar resumes via cosine similarity on embeddings."""
    # Compute job embedding
    q_emb = np.array(llm_client.embed_structured_data(job_description))
    # Normalize embeddings for cosine similarity
    emb_norms = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    q_norm = q_emb / np.linalg.norm(q_emb)
    # Compute similarities and sort descending
    similarities = emb_norms.dot(q_norm)
    idxs = np.argsort(-similarities)
    # Return top_k resumes by similarity
    return [documents[i] for i in idxs[:top_k]]


def evaluate(recommended: List[Document], relevant: List[Document]) -> Dict[str, float]:
    """Evaluate recommendation performance by computing precision, recall, and F1 score."""
    # Extract document IDs for set operations
    recommended_ids = {doc.id for doc in recommended}
    relevant_ids = {doc.id for doc in relevant}
    true_positives = recommended_ids.intersection(relevant_ids)
    precision = len(true_positives) / len(recommended) if recommended else 0.0
    recall = len(true_positives) / len(relevant) if relevant else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def run_pipeline(job_description: str, db_path: Optional[str] = None, model_output_path: Optional[str] = None, top_k: int = 1) -> List[Document]:
    """Run the full pipeline: clean, ingest, train retrieval model, recommend resumes, and save the model."""
    # Determine database path
    if db_path:
        db_file = Path(db_path)
    else:
        db_file = Path(CONSTANTS.USER_HOME_DIR) / CONSTANTS.DB_NAME

    # Initialize repository
    repo = SQLiteDocumentRepository(str(db_file))

    # Fetch only resume documents
    documents = repo.get_by_type(DocumentType.RESUME)

    if not documents:
        logger.warning("No resumes found for pipeline execution.")
        return []

    # Stage 1: Clean
    cleaned_docs = clean(documents)

    # Stage 2: Ingest
    embeddings, docs = ingest(cleaned_docs, llm_client)

    # Stage 3: No-op train (pass embeddings through)
    model = train(embeddings)

    # Stage 4: Predict using embedding similarity
    recommended = predict(job_description, model, docs, llm_client, top_k)
    logger.info(f"Top {top_k} recommended resumes: {[doc.id for doc in recommended]}")

    # Save retrieval model and documents metadata
    if model_output_path:
        model_path = Path(model_output_path)
    else:
        model_path = Path(CONSTANTS.USER_HOME_DIR) / 'retrieval_model.joblib'
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'embeddings': model, 'documents': docs}, str(model_path))
    logger.info(f"Retrieval model saved to {model_path}")

    return recommended


__all__ = ['clean', 'ingest', 'train', 'predict', 'evaluate', 'run_pipeline']
