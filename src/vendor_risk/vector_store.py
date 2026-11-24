import chromadb

_client = chromadb.PersistentClient(path="storage/chroma")
_collection = _client.get_or_create_collection("vendor_risk_documents")


def add_chunks(chunks, embeddings, source_type: str, vendor_id: str):
    """Replace stored chunks for a vendor and source type with new chunks."""
    _collection.delete(
        where={
            "$and": [
                {"vendor_id": vendor_id},
                {"source_type": source_type},
            ]
        }
    )

    if not chunks:
        return

    ids = [
        f"{vendor_id}-{source_type}-{i}"
        for i in range(len(chunks))
    ]

    _collection.add(
        ids=ids,
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "source": c["source"],
                "page": c["page"] or -1,
                "source_type": source_type,
                "vendor_id": vendor_id,
            }
            for c in chunks
        ],
    )


def get_collection():
    """Return the shared persistent Chroma document collection."""
    return _collection