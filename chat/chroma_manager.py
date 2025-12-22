# chat/chroma_manager.py

import os
import chromadb
from chromadb.config import Settings
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv("HF_API_KEY")

# Hugging Face Router client (EMBEDDINGS)
embed_client = InferenceClient(
    model="intfloat/e5-small-v2",
    token=HF_API_KEY,
)

chroma_client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False,
    )
)

def get_collection(conversation_id):
    return chroma_client.get_or_create_collection(
        name=f"conversation_{conversation_id}"
    )

def embed_texts(texts):
    # E5 requires "passage:" and "query:" prefixes
    return embed_client.feature_extraction(
        texts
    )

def add_document_to_chroma(conversation_id, text):
    collection = get_collection(conversation_id)

    chunks = split_text(text)

    passages = [f"passage: {c}" for c in chunks]
    embeddings = embed_texts(passages)

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{conversation_id}_{i}" for i in range(len(chunks))]
    )

def query_document(conversation_id, query, n_results=4):
    collection = get_collection(conversation_id)

    query_embedding = embed_texts([f"query: {query}"])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return results.get("documents", [[]])[0]

def split_text(text, chunk_size=400, overlap=80):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks
