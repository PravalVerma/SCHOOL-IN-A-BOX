# services/ingestion.py
"""
Content ingestion utilities.

Responsible for:
- Loading PDFs from disk
- Splitting raw text into chunks
- Pushing chunks into the vector store

Images will be handled later via the vision model in the explainer agent,
not in this ingestion pipeline.
"""

from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from school_in_a_box.config import CHUNK_SIZE, CHUNK_OVERLAP
from school_in_a_box.services.vector_store import store as vector_store



def _get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Shared text splitter using global chunk settings.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )


# ---------- Raw text ingestion ----------

def chunk_text(text: str) -> List[str]:
    """
    Split a long text string into chunks.

    Returns a list of string chunks.
    """
    splitter = _get_text_splitter()
    docs = splitter.create_documents([text])
    return [d.page_content for d in docs]


def ingest_text(text: str, source_id: str) -> List[str]:
    """
    Ingest a raw text string:

    - Chunk it
    - Add chunks to the vector store with the given source_id
    - Return the chunks
    """
    chunks = chunk_text(text)
    if chunks:
        vector_store.add_texts(chunks, source_id=source_id)
    return chunks


# ---------- PDF ingestion ----------

def load_pdf(path: str | Path) -> List[str]:
    """
    Load a PDF from disk and return a list of text chunks (strings).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    loader = PyPDFLoader(str(path))
    docs = loader.load()

    splitter = _get_text_splitter()
    split_docs = splitter.split_documents(docs)

    return [d.page_content for d in split_docs]


def ingest_pdf(path: str | Path, source_id: str) -> List[str]:
    """
    Ingest a PDF:

    - Load + chunk PDF content
    - Add chunks to the vector store with the given source_id
    - Return the chunks
    """
    chunks = load_pdf(path)
    if chunks:
        vector_store.add_texts(chunks, source_id=source_id)
    return chunks
