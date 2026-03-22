import os
import json
from typing import List, Dict, Optional
from datetime import datetime

import redis


# ---------- Redis connection ----------

_redis_client = None


def _get_redis_client() -> redis.Redis:
    """
    Singleton Redis client.
    Works locally, in Docker, and in production.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6380)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )

    return _redis_client


# ---------- Session metadata ----------

def set_repo_for_session(session_id: str, repo_url: str):
    r = _get_redis_client()
    r.hset(f"session:{session_id}", mapping={"repo_url": repo_url})


def get_repo_for_session(session_id: str) -> Optional[str]:
    r = _get_redis_client()
    return r.hget(f"session:{session_id}", "repo_url")



def create_conversation(session_id: str, conversation_id: str, title: str = "New Chat") -> Dict:
    """
    Creates a new conversation thread for a session.
    """
    r = _get_redis_client()
    
    conversation_data = {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "message_count": "0"
    }
    
    # Store conversation metadata
    r.hset(f"conversation:{conversation_id}", mapping=conversation_data)
    
    # Add to session's conversation list (sorted set by timestamp)
    timestamp = datetime.utcnow().timestamp()
    r.zadd(f"session:{session_id}:conversations", {conversation_id: timestamp})
    
    return conversation_data


def get_all_conversations(session_id: str) -> List[Dict]:
    """
    Get all conversations for a session, sorted by most recent.
    """
    r = _get_redis_client()
    
    # Get conversation IDs sorted by timestamp (newest first)
    conversation_ids = r.zrevrange(f"session:{session_id}:conversations", 0, -1)
    
    conversations = []
    for conv_id in conversation_ids:
        conv_data = r.hgetall(f"conversation:{conv_id}")
        if conv_data:
            conversations.append(conv_data)
    
    return conversations


def get_conversation_metadata(conversation_id: str) -> Optional[Dict]:
    """
    Get metadata for a specific conversation.
    """
    r = _get_redis_client()
    return r.hgetall(f"conversation:{conversation_id}")


def update_conversation_title(conversation_id: str, title: str):
    """
    Update conversation title (useful for auto-generating from first message).
    """
    r = _get_redis_client()
    r.hset(f"conversation:{conversation_id}", "title", title)
    r.hset(f"conversation:{conversation_id}", "updated_at", datetime.utcnow().isoformat())


def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages.
    """
    r = _get_redis_client()
    
    # Get session_id to remove from session's conversation list
    conv_data = r.hgetall(f"conversation:{conversation_id}")
    if conv_data and "session_id" in conv_data:
        session_id = conv_data["session_id"]
        r.zrem(f"session:{session_id}:conversations", conversation_id)
    
    # Delete conversation metadata and messages
    r.delete(f"conversation:{conversation_id}")
    r.delete(f"chat:{conversation_id}")



def add_message(conversation_id: str, role: str, content: str, sources: List[str] = None):
    """
    Add a message to a conversation (changed from session_id to conversation_id).
    """
    r = _get_redis_client()

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if sources:
        message["sources"] = sources

    r.rpush(f"chat:{conversation_id}", json.dumps(message))
    
    # Update conversation metadata
    r.hincrby(f"conversation:{conversation_id}", "message_count", 1)
    r.hset(f"conversation:{conversation_id}", "updated_at", datetime.utcnow().isoformat())


def get_chat_history(
    conversation_id: str,  
    limit: int = 20,
) -> List[Dict[str, str]]:
    """
    Get chat history for a conversation (changed from session_id to conversation_id).
    """
    r = _get_redis_client()

    raw_messages = r.lrange(f"chat:{conversation_id}", -limit, -1)
    return [json.loads(m) for m in raw_messages]


def clear_chat(conversation_id: str): 
    """
    Clear chat history for a conversation.
    """
    r = _get_redis_client()
    r.delete(f"chat:{conversation_id}")
    r.hset(f"conversation:{conversation_id}", "message_count", "0")