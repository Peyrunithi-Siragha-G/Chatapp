import chromadb

client = chromadb.Client()

def get_collection(conversation_id):
    return client.get_or_create_collection(
        name=f"conv_{conversation_id}"
    )

def add_document_to_chroma(conversation_id, text):
    collection = get_collection(conversation_id)

    collection.add(
        documents=[text],
        ids=[str(len(collection.get()["ids"]) + 1)]
    )

def query_document(conversation_id, query):
    collection = get_collection(conversation_id)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    return results.get("documents", [[]])[0]
