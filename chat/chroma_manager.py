import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Load embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client(
    Settings(persist_directory="chroma_db", anonymized_telemetry=False)
)

def get_collection(conversation_id):
    return client.get_or_create_collection(
        name=f"conversation_{conversation_id}"
    )

def add_document(conversation_id, text):
    collection = get_collection(conversation_id)

    chunks = split_text(text)

    embeddings = embedding_model.encode(chunks).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{conversation_id}_{i}" for i in range(len(chunks))]
    )

def query_document(conversation_id, query, top_k=3):
    collection = get_collection(conversation_id)

    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return results["documents"][0] if results["documents"] else []

def split_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks
