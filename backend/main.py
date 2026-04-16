import os
import uuid
import asyncio
import re
import logging
import tempfile
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

import shutil
from fastapi.responses import FileResponse
from services.code_editor import (
    analyze_modification_intent,
    generate_code_changes,
    apply_modifications,
    create_patch_file,
    create_zip_archive
)

# Add to existing imports
from typing import Optional

# New request model
class CodeModificationRequest(BaseModel):
    session_id: str
    modification_query: str
    conversation_id: Optional[str] = None

# Store modification sessions (in production, use database)
modification_sessions: Dict[str, dict] = {}

@app.post("/api/modify-code")
async def modify_code(request: CodeModificationRequest):
    """
    Analyze code modification request and generate changes.
    """
    session_id = request.session_id
    query = request.modification_query.strip()
    
    if session_id not in sessions or sessions[session_id]["status"] != "ready":
        raise HTTPException(status_code=404, detail="Session not found or not ready")
    
    logger.info(f"Code modification request - Session: {session_id}, Query: {query}")
    
    try:
        # Get collection and search for relevant files
        collection = get_collection(session_id)
        context_chunks = await asyncio.to_thread(search, collection, query, 10)
        
        logger.info(f"Found {len(context_chunks)} relevant code chunks")
        
        # Analyze modification intent
        intent_analysis = await analyze_modification_intent(query, context_chunks)
        
        logger.info(f"Intent analysis: {intent_analysis}")
        
        # Get original repo path (reconstruct from session)
        repo_url = sessions[session_id]["repo_url"]
        
        # Clone repo again for modification (fresh copy)
        repo_path = await asyncio.to_thread(clone_repo, repo_url)
        
        # Generate modifications for each target file
        modifications = []
        
        for idx, target_file in enumerate(intent_analysis['target_files'][:2]):  # Limit to 2 files to avoid rate limits
            # Add delay between API calls to avoid hitting rate limits
            if idx > 0:
                await asyncio.sleep(2)
                
            # Find this file in context chunks
            file_chunks = [c for c in context_chunks if target_file in c['file_path']]
            
            if not file_chunks:
                continue
            
            # Read original file content
            file_full_path = os.path.join(repo_path, target_file)
            
            if not os.path.exists(file_full_path):
                continue
            
            with open(file_full_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Generate modified code
            modified_content = await generate_code_changes(
                file_path=target_file,
                file_content=original_content,
                modification_request=query,
                file_context=file_chunks
            )
            
            modifications.append({
                "file_path": target_file,
                "original_content": original_content,
                "modified_content": modified_content
            })
        
        if not modifications:
            raise HTTPException(status_code=400, detail="No files could be modified")
        
        # Apply modifications
        result = await asyncio.to_thread(
            apply_modifications,
            repo_path,
            modifications,
            session_id
        )
        
        # Create modification session
        mod_session_id = str(uuid.uuid4()).replace("-", "")[:16]
        
        # Create patch file
        patch_path = os.path.join(tempfile.gettempdir(), f"{mod_session_id}.patch")
        create_patch_file(result['diffs'], patch_path)
        
        # Create zip of modified repo
        zip_path = os.path.join(tempfile.gettempdir(), f"{mod_session_id}_modified.zip")
        create_zip_archive(result['modified_repo_path'], zip_path)
        
        # Store modification session
        modification_sessions[mod_session_id] = {
            "original_repo_path": repo_path,
            "modified_repo_path": result['modified_repo_path'],
            "patch_path": patch_path,
            "zip_path": zip_path,
            "diffs": result['diffs'],
            "summary": result['summary'],
            "files_changed": result['files_changed'],
            "created_at": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Modification session created: {mod_session_id}")
        
        return {
            "modification_id": mod_session_id,
            "summary": result['summary'],
            "files_changed": result['files_changed'],
            "diffs": result['diffs'],
            "intent_analysis": intent_analysis
        }
        
    except Exception as e:
        logger.error(f"Error in code modification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code modification failed: {str(e)}")


@app.get("/api/download-patch/{modification_id}")
async def download_patch(modification_id: str):
    """
    Download patch file for code modifications.
    """
    if modification_id not in modification_sessions:
        raise HTTPException(status_code=404, detail="Modification session not found")
    
    patch_path = modification_sessions[modification_id]['patch_path']
    
    return FileResponse(
        path=patch_path,
        filename=f"repochat_changes_{modification_id}.patch",
        media_type="text/plain"
    )


@app.get("/api/download-modified-repo/{modification_id}")
async def download_modified_repo(modification_id: str):
    """
    Download zip archive of modified repository.
    """
    if modification_id not in modification_sessions:
        raise HTTPException(status_code=404, detail="Modification session not found")
    
    zip_path = modification_sessions[modification_id]['zip_path']
    
    return FileResponse(
        path=zip_path,
        filename=f"repochat_modified_{modification_id}.zip",
        media_type="application/zip"
    )


@app.get("/api/modification-status/{modification_id}")
def get_modification_status(modification_id: str):
    """
    Get details of a modification session.
    """
    if modification_id not in modification_sessions:
        raise HTTPException(status_code=404, detail="Modification session not found")
    
    session = modification_sessions[modification_id]
    
    return {
        "modification_id": modification_id,
        "summary": session['summary'],
        "files_changed": session['files_changed'],
        "diffs": session['diffs']
    }