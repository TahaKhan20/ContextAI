from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
import shutil
from rag.session_manager import SessionManager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas.rename import RenameRequest

from schemas.chat import ChatRequest

from rag.indexing import build_index
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.prompt import build_prompt
from rag.llm import ask_llm
from rag.query_rewriter import rewrite_query
from rag.loader import SUPPORTED_EXTENSIONS


# ==========================
# Constants
# ==========================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

INDEX_PATH = "storage/index.faiss"
METADATA_PATH = "storage/metadata.pkl"


# ==========================
# Global Objects
# ==========================

embedder = Embedder()
session_manager = SessionManager()

stores = {}

def get_store(session_id: str):

    if session_id in stores:
        return stores[session_id]

    index = Path("storage") / session_id / "index.faiss"
    metadata = Path("storage") / session_id / "metadata.pkl"

    if not index.exists():
        return None

    store = VectorStore.load(
        str(index),
        str(metadata)
    )

    stores[session_id] = store

    return store

# ==========================
# FastAPI App
# ==========================

app = FastAPI(title="RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# Home
# ==========================

@app.get("/")
def home():
    return {
        "message": "RAG API is running 🚀"
    }


# ==========================
# Upload Documents
# ==========================

@app.post("/upload/{session_id}")
async def upload_documents(
    session_id: str,
    files: List[UploadFile] = File(...)
):

    # Validate all files by extension
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{file.filename}' has an unsupported format. "
                    f"Accepted types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                )
            )

    session_upload_dir = Path("uploads") / session_id
    session_upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )
    uploaded = []

    for file in files:

        filename = Path(file.filename).name
        path = session_upload_dir / filename

        if path.exists():
            print(f"{filename} already uploaded.")
        else:
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        await file.close()

        uploaded.append(filename)

    return {
        "status": "success",
        "uploaded": uploaded,
        "count": len(uploaded)
    }


# ==========================
# Build Index
# ==========================

@app.post("/index/{session_id}")
def index_documents(session_id: str):

    storage_dir = Path("storage") / session_id
    storage_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        chunk_count = build_index(

            embedder=embedder,

            upload_dir=f"uploads/{session_id}",

            index_path=f"storage/{session_id}/index.faiss",

            metadata_path=f"storage/{session_id}/metadata.pkl"

        )

        stores[session_id] = VectorStore.load(

            f"storage/{session_id}/index.faiss",

            f"storage/{session_id}/metadata.pkl"

        )

        return {
            "status": "success",
            "chunks": chunk_count
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print(e)

        raise HTTPException(
            status_code=500,
            detail="Failed to build index."
        )
 
# ==========================
# Session Management
# ==========================
@app.post("/sessions")
def create_session():

    session = session_manager.create_session()

    return session

@app.get("/sessions")
def list_sessions():

    return session_manager.list_sessions()

@app.get("/sessions/{session_id}")
def get_session(session_id: str):

    history = session_manager.get_history(session_id)

    return {
        "session_id": session_id,
        "messages": history
    }

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):

    session_manager.delete_session(session_id)

    stores.pop(session_id, None)

    return {
        "status": "deleted"
    }


@app.put("/sessions/{session_id}")
def rename_session(
    session_id: str,
    request: RenameRequest
):

    session = session_manager.rename_session(
        session_id,
        request.title
    )

    if session is None:

        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    return session

# ==========================
# Chat
# ==========================

@app.post("/chat/{session_id}")
def chat(
    session_id: str,
    request: ChatRequest
):


    store = get_store(session_id)

    if store is None:
        raise HTTPException(
            status_code=400,
            detail="No index found for this session."
        )

    session_manager.add_message(
        session_id,
        "user",
        request.question
    )


    messages = session_manager.get_history(
        session_id
    )
    standalone_question = rewrite_query(
        request.question,
        messages
    )

    query = embedder.embed_text(
        standalone_question
    )

    results = store.search(
        query,
        k=5
    )

    prompt = build_prompt(
        question=standalone_question,
        retrieved_chunks=results,
        history=messages
    )

    answer = ask_llm(prompt)

    session_manager.add_message(
        session_id,
        "assistant",
        answer
    )

    return {
        "question": request.question,
        "rewritten_question": standalone_question,
        "answer": answer,
        "sources": results
    }


    
