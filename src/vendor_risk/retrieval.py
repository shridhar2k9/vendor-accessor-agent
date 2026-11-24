from .embedding import embed_texts
from .vector_store import get_collection


def retrieve(query: str, vendor_id: str, source_type: str, k: int = 4) -> list[dict]:
    """Retrieve the closest evidence passages for a vendor and source type."""
    collection = get_collection()
    query_embedding = embed_texts([query])[0]

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={
            "$and": [
                {"vendor_id": vendor_id},
                {"source_type": source_type},
            ]
        },
    )

    passages = []
    for text, metadata in zip(
        result["documents"][0],
        result["metadatas"][0],
    ):
        passages.append({
            "text": text,
            "source": metadata["source"],
            "page": metadata["page"] if metadata["page"] >= 1 else None,
        })

    return passages