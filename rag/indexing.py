from pathlib import Path

from rag.loader import load_document, SUPPORTED_EXTENSIONS
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
    upload_path = Path(upload_dir)

    for file in upload_path.iterdir():

        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        print(f"Indexing {file.name}")

        try:
            pages = load_document(str(file))
        except Exception as e:
            print(f"Skipping {file.name}: {e}")
            continue

        chunks = chunk_pages(pages)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No supported documents found.")

    texts = [chunk["text"] for chunk in all_chunks]

    embeddings = embedder.embed_documents(texts)

    store = VectorStore(embeddings.shape[1])

    store.add(embeddings, all_chunks)

    store.save(index_path, metadata_path)

    return len(all_chunks)
