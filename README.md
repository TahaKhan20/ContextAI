# ContextAI

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you upload documents and chat with them using AI. ContextAI extracts text from your files, builds a semantic search index, and answers questions with accurate, source-backed responses.

ContextAI website: https://context-ai.mohammadtahakhan20.workers.dev/

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1--mini-purple)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-orange)

---

## Features

- **Multi-Format Upload** — Upload PDFs, Word documents, Excel spreadsheets, PowerPoint presentations, CSVs, and plain text files
- **Semantic Search** — FAISS-powered vector similarity search using sentence-transformers
- **Conversational Memory** — Chat history with context-aware query rewriting
- **Source Citations** — Every answer references the document name and page number
- **Session Management** — Create, rename, and delete independent chat sessions
- **Dark-themed UI** — Responsive ChatGPT-style frontend

---

## Supported File Types

| Format | Extension(s) | Library |
| --- | --- | --- |
| PDF | `.pdf` | `pypdf` |
| Word | `.docx` | `python-docx` |
| Excel | `.xlsx`, `.xls` | `pandas`, `openpyxl`, `xlrd` |
| PowerPoint | `.pptx` | `python-pptx` |
| CSV | `.csv` | `pandas` |
| Plain Text | `.txt` | built-in |

---

## Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Query Rewriter │  ← Rewrites follow-up questions into standalone queries
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Embedder     │  ← Encodes query using sentence-transformers (all-MiniLM-L6-v2)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FAISS Index    │  ← Cosine similarity search over document chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prompt Builder │  ← Combines context + history + question into a prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OpenAI LLM    │  ← Generates the final answer (GPT-4.1-mini)
└─────────────────┘
```

---

## Project Structure

```
ContextAI/
├── app.py                  # FastAPI application (routes & endpoints)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore
│
├── rag/                    # RAG pipeline modules
│   ├── loader.py           # Document loader — PDF, DOCX, XLSX, XLS, PPTX, CSV, TXT
│   ├── cleaner.py          # Text cleaning & normalization
│   ├── chunker.py          # Sliding-window text chunking
│   ├── embedder.py         # Sentence-transformer embeddings
│   ├── vector_store.py     # FAISS index wrapper (add, search, save, load)
│   ├── indexing.py         # Orchestrates load → chunk → embed → store
│   ├── prompt.py           # Prompt template builder
│   ├── llm.py              # OpenAI API wrapper
│   ├── query_rewriter.py   # Conversation-aware query rewriting
│   ├── session_manager.py  # JSON-based session CRUD
│   └── memory.py           # (Reserved for future memory features)
│
├── schemas/                # Pydantic request models
│   ├── chat.py             # ChatRequest schema
│   └── rename.py           # RenameRequest schema
│
├── frontend/               # Static web UI
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── favicon.svg
│
├── uploads/                # Uploaded documents (per session)
├── storage/                # FAISS indexes & metadata (per session)
└── sessions/               # Session data (sessions.json)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ContextAI.git
cd ContextAI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 5. Run the Backend

```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

### 6. Open the Frontend

Open `frontend/index.html` directly in your browser, or serve it with any static file server:

```bash
# Option: Python's built-in server
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`.

---

## API Reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Health check |
| `POST` | `/sessions` | Create a new chat session |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/sessions/{id}` | Get session with message history |
| `PUT` | `/sessions/{id}` | Rename a session |
| `DELETE` | `/sessions/{id}` | Delete a session and its data |
| `POST` | `/upload/{id}` | Upload documents to a session |
| `POST` | `/index/{id}` | Build the FAISS index for a session |
| `POST` | `/chat/{id}` | Ask a question against the indexed documents |

### Example: Chat Request

```bash
curl -X POST http://127.0.0.1:8000/chat/SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the document?"}'
```

---

## How It Works (Step by Step)

### 1. Document Upload & Text Extraction

When you upload files, the backend saves them to `uploads/{session_id}/`. The **loader** (`rag/loader.py`) dispatches to a format-specific extractor based on file extension — `pypdf` for PDFs, `python-docx` for Word, `pandas` for Excel/CSV, `python-pptx` for PowerPoint, and the built-in `open()` for plain text. The **cleaner** (`rag/cleaner.py`) then normalizes whitespace and removes noise.

### 2. Chunking

The **chunker** (`rag/chunker.py`) splits each page into overlapping text chunks using a sliding window:

- **Chunk size:** 700 characters
- **Overlap:** 150 characters
- **Minimum chunk length:** 100 characters

Each chunk retains its source file name and page number (or sheet name for Excel) for citations.

### 3. Embedding & Indexing

The **embedder** (`rag/embedder.py`) encodes all chunks using `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings). These are stored in a **FAISS** index (`rag/vector_store.py`) using inner-product (cosine) similarity after L2 normalization.

### 4. Query Processing

When you ask a question:

1. The **query rewriter** (`rag/query_rewriter.py`) uses the LLM to resolve pronouns and make the question standalone based on conversation history.
2. The rewritten question is embedded and searched against the FAISS index (top 5 results).
3. The **prompt builder** (`rag/prompt.py`) assembles the retrieved chunks + history into a structured prompt.
4. The **LLM** (`rag/llm.py`) generates the final answer via OpenAI's API.

### 5. Session Management

All sessions are stored in `sessions/sessions.json`. Each session tracks its title, creation time, and full message history. Uploaded files and indexes are stored in per-session directories.

---

## Customization Guide

### Swap the Embedding Model

Edit `rag/embedder.py`:

```python
# Change the model name to any sentence-transformers model
self.model = SentenceTransformer("all-mpnet-base-v2")  # 768-dim, higher quality
```

> Note: Changing the model changes the embedding dimension. Existing indexes will need to be rebuilt.

### Swap the LLM

Edit `rag/llm.py`:

```python
# Use a different OpenAI model
model="gpt-4o"          # More capable, higher cost
model="gpt-4o-mini"    # Balanced
model="gpt-3.5-turbo"  # Cheapest
```

Or replace with any OpenAI-compatible API (Ollama, Azure OpenAI, etc.) by changing the `client` initialization.

### Adjust Chunking Strategy

Edit `rag/chunker.py`:

```python
chunk_size=1000    # Larger chunks = more context per result
overlap=200        # More overlap = less information loss at boundaries
```

### Change the Number of Retrieved Results

Edit the `k` parameter in `app.py` → `chat()`:

```python
results = store.search(query, k=10)  # Retrieve more chunks
```

### Add Support for New File Types

Add a loader function in `rag/loader.py`, register the extension in `SUPPORTED_EXTENSIONS`, and add a branch in `load_document()`. No other files need to change.

### Use a Different Vector Database

Replace `rag/vector_store.py` with a wrapper around:

- **ChromaDB** — Persistent, supports metadata filtering
- **Pinecone** — Managed cloud vector database
- **Qdrant** — Open-source with rich filtering
- **Weaviate** — Schema-aware vector search

---

## Production Deployment

### With Gunicorn (Linux/macOS)

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### With Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```env
OPENAI_API_KEY=sk-...
```

---

## Limitations

- **No streaming** — Responses are returned in full (streaming support is scaffolded but not active)
- **JSON file storage** — Sessions are stored in a flat JSON file; not suitable for high-concurrency production use
- **In-memory FAISS** — Indexes are loaded into RAM; large document sets may require a persistent vector database

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is open-source. Feel free to use, modify, and distribute it for your own RAG applications.
