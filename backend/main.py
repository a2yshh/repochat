import uuid
import asyncio
import re
import logging
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

from services.repo_process import clone_repo, get_code_files, cleanup_repo
from services.code_chunk import chunk_code_file
from services.vector_storing import create_collection, get_collection, add_chunks, search
from services.llm_service import generate_response_stream
from services.redis_service import (
    set_repo_for_session,
    create_conversation,
    get_all_conversations,
    get_conversation_metadata,
    delete_conversation,
    get_chat_history
)

app = FastAPI(title="RepoChat API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}

# ---------------- MODELS ----------------

class ProcessRepoRequest(BaseModel):
    github_url: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation_id: Optional[str] = None

# ---------------- HEALTH ----------------

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/status/{session_id}")
def get_status(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

# ---------------- BACKGROUND PROCESSING ----------------

async def process_repo_background(session_id: str, github_url: str):
    repo_path = None

    try:
        logger.info(f"[{session_id}] STEP 1: Cloning repo")
        sessions[session_id]["status"] = "cloning"

        repo_path = await asyncio.to_thread(clone_repo, github_url)

        logger.info(f"[{session_id}] STEP 2: Getting files")
        sessions[session_id]["status"] = "processing"

        code_files = await asyncio.to_thread(get_code_files, repo_path)
        sessions[session_id]["files_processed"] = len(code_files)

        if not code_files:
            raise Exception("No code files found")

        logger.info(f"[{session_id}] Found {len(code_files)} files")

       
        code_files = code_files[:50]

        logger.info(f"[{session_id}] STEP 3: Chunking")
        all_chunks = []

        for file_path in code_files:
            chunks = chunk_code_file(file_path, repo_path)
            all_chunks.extend(chunks)

        logger.info(f"[{session_id}] Created {len(all_chunks)} chunks")

        sessions[session_id]["status"] = "embedding"

        logger.info(f"[{session_id}] STEP 4: Creating embeddings")

        collection = create_collection(session_id)

        
        batch_size = 20

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]

            logger.info(f"[{session_id}] Embedding batch {i} → {i+len(batch)}")

            await asyncio.to_thread(add_chunks, collection, batch)

        sessions[session_id] = {
            "status": "ready",
            "files_processed": len(code_files),
            "total_chunks": len(all_chunks),
            "repo_url": github_url,
        }

        await asyncio.to_thread(set_repo_for_session, session_id, github_url)

        logger.info(f"[{session_id}] ✅ READY")

    except Exception as e:
        logger.error(f"[{session_id}] ❌ ERROR: {e}", exc_info=True)
        sessions[session_id]["status"] = "error"

    finally:
        if repo_path:
            cleanup_repo(repo_path)

# ---------------- PROCESS REPO ----------------

@app.post("/api/process-repo")
async def process_repo(request: ProcessRepoRequest):
    session_id = str(uuid.uuid4()).replace("-", "")[:16]
    github_url = request.github_url.strip()

    github_pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
    if not re.match(github_pattern, github_url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    sessions[session_id] = {
        "status": "starting",
        "files_processed": 0
    }

    # 🔥 BACKGROUND TASK
    asyncio.create_task(process_repo_background(session_id, github_url))

    return {
        "session_id": session_id,
        "status": "processing"
    }

# ---------------- CHAT ----------------

@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message.strip()
    conversation_id = request.conversation_id

    if not message:
        raise HTTPException(status_code=400, detail="Empty message")

    if session_id not in sessions or sessions[session_id]["status"] != "ready":
        raise HTTPException(status_code=400, detail="Session not ready")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        title = message[:50]

        await asyncio.to_thread(
            create_conversation,
            session_id,
            conversation_id,
            title
        )

    collection = get_collection(session_id)

    context_chunks = await asyncio.to_thread(
        search,
        collection,
        message,
        5
    )

    sources = list({chunk["file_path"] for chunk in context_chunks})

    async def stream_response():
        async for token in generate_response_stream(
            conversation_id,
            message,
            context_chunks
        ):
            yield token
        yield "\n\n---SOURCES---\n" + "\n".join(sources)

    return StreamingResponse(
        stream_response(),
        media_type="text/plain",
        headers={"X-Conversation-ID": conversation_id}
    )

# ---------------- CONVERSATIONS ----------------

@app.get("/api/conversations/{session_id}")
async def get_conversations(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    conversations = await asyncio.to_thread(
        get_all_conversations,
        session_id
    )

    return {"conversations": conversations}


@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    metadata = await asyncio.to_thread(
        get_conversation_metadata,
        conversation_id
    )

    if not metadata:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = await asyncio.to_thread(
        get_chat_history,
        conversation_id,
        100
    )

    return {
        "metadata": metadata,
        "messages": history
    }


@app.delete("/api/conversation/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    await asyncio.to_thread(delete_conversation, conversation_id)
    return {"status": "deleted"}