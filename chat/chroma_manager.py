# chat/chroma_manager.py
import os
import logging

logger = logging.getLogger(__name__)

USE_CHROMA = os.getenv("USE_CHROMA", "0") == "1"

if USE_CHROMA:
    try:
        import chromadb
        CHROMA_PATH = os.getenv("CHROMA_PATH", "/tmp/chroma")
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = chroma_client.get_or_create_collection(name="documents")
    except Exception as e:
        logger.exception("Failed to init Chroma: %s", e)
        USE_CHROMA = False
        collection = None
else:
    collection = None


def add_document_to_chroma(doc_id, text):
    if not USE_CHROMA or collection is None:
        logger.info("Chroma disabled — not adding embeddings.")
        return False
    try:
        # make sure text is non-empty
        if not text or not text.strip():
            return False
        collection.add(ids=[str(doc_id)], documents=[text])
        return True
    except Exception as e:
        logger.exception("Chroma add failed: %s", e)
        return False


def search_relevant_text(query, top_k=3):
    """
    If Chroma enabled: run query, return concatenated documents.
    Otherwise: return empty string (caller should fallback to returning full doc text).
    """
    if not USE_CHROMA or collection is None:
        return ""
    try:
        results = collection.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [])
        if docs and len(docs) > 0:
            # docs is list-of-lists
            return "\n\n".join(docs[0])
    except Exception as e:
        logger.exception("Chroma query failed: %s", e)
    return ""
