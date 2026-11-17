def chunk_pages(pages: list[dict], size: int = 1000, overlap: int = 150):
    chunks = []

    for item in pages:
        text = item["text"]
        start = 0

        while start < len(text):
            end = min(start + size, len(text))
            chunks.append({
                **item,
                "text": text[start:end],
            })

            if end == len(text):
                break
            start = end - overlap

    return chunks