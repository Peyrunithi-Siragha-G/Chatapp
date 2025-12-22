import chromadb
import requests
import os

HF_TOKEN = os.getenv("HF_API_KEY")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="chroma_db",
        anonymized_telemetry=False
    )
)

def embed(texts):
    response = requests.post(
        f"https://router.huggingface.co/hf-inference/models/{EMBEDDING_MODEL}",
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json={"inputs": texts}
    )
    response.raise_for_status()
    return [item["embedding"] for item in response.json()]

def get_collection(conversation_id):
    return client.get_or_create_collection(
        name=f"conversation_{conversation_id}"
    )

def add_document(conversation_id, text):
    chunks = split_text(text)
    embeddings = embed(chunks)

    collection = get_collection(conversation_id)
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{conversation_id}_{i}" for i in range(len(chunks))]
    )

def query_document(conversation_id, query, top_k=3):
    collection = get_collection(conversation_id)
    query_embedding = embed([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results["documents"][0] if results["documents"] else []

def split_text(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunks
