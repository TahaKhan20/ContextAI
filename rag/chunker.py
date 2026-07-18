from typing import List


def chunk_pages(
    pages,
    chunk_size=700,
    overlap=150
):

    chunks = []

    step = chunk_size - overlap

    for page in pages:

        text = page["text"]

        start = 0

        while start < len(text):

            end = min(start + chunk_size, len(text))

            chunk = text[start:end].strip()

            if len(chunk) > 100:

                chunks.append({
                    "source": page["source"],
                    "page": page["page"],
                    "text": chunk
                })

            if end == len(text):
                break

            start += step

    return chunks