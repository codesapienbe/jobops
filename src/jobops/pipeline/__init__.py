from typing import List, Tuple, Any, Dict
import logging
from pathlib import Path
import os
import re

from jobops.models import Document, DocumentType
from jobops.repositories import SQLiteDocumentRepository
from jobops.config import CONSTANTS, JSONConfigManager

from jobops.clients import embed_structured_data, LLMBackendFactory
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


def ingest(documents: List[Document]) -> Tuple[List[List[float]], List[Document]]:
    """Convert documents into embedding vectors and keep document references."""
    embeddings_list: List[List[float]] = []
    for doc in documents:
        content = doc.structured_content or doc.raw_content
        emb = embed_structured_data(content)
        embeddings_list.append(emb)
    embeddings = np.array(embeddings_list)
    return embeddings, documents


def train(embeddings: np.ndarray) -> np.ndarray:
    """Pass through embeddings array for similarity lookup."""
    return embeddings


def predict(job_description: str, embeddings: np.ndarray, documents: List[Document], top_k: int = 1) -> List[Document]:
    """Given a new job description, find the top_k most similar resumes via cosine similarity on embeddings."""
    # Compute job embedding
    q_emb = np.array(embed_structured_data(job_description))
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


def run_pipeline(job_description: str, db_path: str = None, model_output_path: str = None, top_k: int = 1) -> List[Document]:
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
    embeddings, docs = ingest(cleaned_docs)

    # Stage 3: No-op train (pass embeddings through)
    model = train(embeddings)

    # Stage 4: Predict using embedding similarity
    recommended = predict(job_description, model, docs, top_k)
    logger.info(f"Top {top_k} recommended resumes: {[doc.filename or doc.id for doc in recommended]}")

    # Save retrieval model and documents metadata
    if model_output_path:
        model_path = Path(model_output_path)
    else:
        model_path = Path(CONSTANTS.USER_HOME_DIR) / 'retrieval_model.joblib'
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'embeddings': model, 'documents': docs}, str(model_path))
    logger.info(f"Retrieval model saved to {model_path}")

    return recommended


def generate_custom_resume(job_description: str, db_path: str = None, llm_backend=None) -> str:
    """
    Retrieve the top resume via the pipeline, then use an LLM to generate a custom resume tailored to the given job description.
    """
    # Get the best matching resume
    recommended = run_pipeline(job_description, db_path=db_path, top_k=1)
    if not recommended:
        logger.warning("No resume found to customize.")
        return ""
    base_resume = recommended[0]
    # Instantiate backend if not provided
    if llm_backend is None:
        config_path = Path(CONSTANTS.USER_HOME_DIR) / CONSTANTS.CONFIG_NAME
        config_manager = JSONConfigManager(str(config_path))
        app_config = config_manager.load()
        backend_type = app_config.backend
        settings = app_config.backend_settings.get(backend_type, {})
        # Gather tokens from environment variables
        tokens = {key: os.getenv(f"{key.upper()}_API_KEY", "") for key in app_config.backend_settings}
        llm_backend = LLMBackendFactory.create(backend_type, settings, tokens)
    # Build prompt for customization
    prompt = (
        f"Rewrite this resume to be specifically tailored for the following job description:\n"
        f"\nJob Description:\n{job_description}\n"
        f"\nBase Resume:\n{base_resume.structured_content}\n"
        "Return the resume in plain text or markdown, preserving standard sections."
    )
    return llm_backend.generate_response(prompt)


__all__ = ['clean', 'ingest', 'train', 'predict', 'evaluate', 'run_pipeline']
