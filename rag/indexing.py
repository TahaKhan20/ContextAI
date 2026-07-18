from pathlib import Path

from rag.loader import load_pdf
from rag.chunker import chunk_pages
from rag.embedder import Embedder
from rag.vector_store import VectorStore


def build_index(
    embedder: Embedder,
    upload_dir="uploads",
    index_path="storage/index.faiss",
    metadata_path="storage/metadata.pkl"
):
    all_chunks = []

    for pdf in Path(upload_dir).glob("*.pdf"):

        print(f"Indexing {pdf.name}")

        pages = load_pdf(str(pdf))

        chunks = chunk_pages(pages)

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No PDF files found.")

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    embeddings = embedder.embed_documents(texts)

    store = VectorStore(
        embeddings.shape[1]
    )

    store.add(
        embeddings,
        all_chunks
    )

    store.save(
        index_path,
        metadata_path
    )

    return len(all_chunks)