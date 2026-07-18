import faiss
import pickle
import numpy as np


class VectorStore:
    def __init__(self, dimension: int):
        """
        Create a FAISS vector store using cosine similarity.
        """
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []

    def add(self, embeddings: np.ndarray, chunks: list):
        """
        Add embeddings and their corresponding chunks to the index.
        """

        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embeddings ({len(embeddings)}) and chunks ({len(chunks)}) must have the same length."
            )

        embeddings = embeddings.astype(np.float32)
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)
        self.documents.extend(chunks)

    def search(self, query_embedding: np.ndarray, k: int = 5):
        """
        Search the vector store and return the top-k most similar chunks.
        """

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        query_embedding = query_embedding.astype(np.float32)
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, k)

        results = []

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            results.append({
                "source": self.documents[idx]["source"],
                "page": self.documents[idx]["page"],
                "text": self.documents[idx]["text"],
                "score": float(score)
            })

        return results

    def save(self, index_path: str, metadata_path: str):
        """
        Save FAISS index and metadata.
        """

        faiss.write_index(self.index, index_path)

        with open(metadata_path, "wb") as f:
            pickle.dump(self.documents, f)

    @classmethod
    def load(cls, index_path: str, metadata_path: str):
        """
        Load a previously saved FAISS index and metadata.
        """

        index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:
            documents = pickle.load(f)

        store = cls(index.d)
        store.index = index
        store.documents = documents

        return store