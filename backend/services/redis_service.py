import os
import json
from typing import List, Dict, Optional
from datetime import datetime

import redis

# ---------- Redis connection ----------

_redis_client = None


def _get_redis_client() -> redis.Redis:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )
        print("REDIS CONNECTED")

        
        try:
            _redis_client.ping()
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}")

    return _redis_client


# ---------- Session ----------

def set_repo_for_session(session_id: str, repo_url: str):
    r = _get_redis_client()
    r.hset(f"session:{session_id}", mapping={
        "repo_url": repo_url
    })


def get_repo_for_session(session_id: str) -> Optional[str]:
    r = _get_redis_client()
    return r.hget(f"session:{session_id}", "repo_url")


# ---------- Conversations ----------

def create_conversation(session_id: str, conversation_id: str, title: str = "New Chat") -> Dict:
    r = _get_redis_client()

    now = datetime.utcnow().isoformat()

    conversation_data = {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "message_count": "0"
    }
    print("CREATING CONVERSATION", session_id, conversation_id)

    for key, value in conversation_data.items():
        r.hset(f"conversation:{conversation_id}", key, value)

    timestamp = datetime.utcnow().timestamp()
    r.zadd(f"session:{session_id}:conversations", {conversation_id: timestamp})

    return conversation_data


def get_all_conversations(session_id: str) -> List[Dict]:
    r = _get_redis_client()

    conversation_ids = r.zrevrange(f"session:{session_id}:conversations", 0, -1)

    conversations = []
    for conv_id in conversation_ids:
        data = r.hgetall(f"conversation:{conv_id}")
        if data:
            conversations.append(data)

    return conversations


def get_conversation_metadata(conversation_id: str) -> Optional[Dict]:
    r = _get_redis_client()
    return r.hgetall(f"conversation:{conversation_id}")


def update_conversation_title(conversation_id: str, title: str):
    r = _get_redis_client()

    r.hset(f"conversation:{conversation_id}", mapping={
        "title": title,
        "updated_at": datetime.utcnow().isoformat()
    })


def delete_conversation(conversation_id: str):
    r = _get_redis_client()

    conv_data = r.hgetall(f"conversation:{conversation_id}")
    if conv_data and "session_id" in conv_data:
        session_id = conv_data["session_id"]
        r.zrem(f"session:{session_id}:conversations", conversation_id)

    r.delete(f"conversation:{conversation_id}")
    r.delete(f"chat:{conversation_id}")


# ---------- Messages ----------

def add_message(conversation_id: str, role: str, content: str, sources: List[str] = None):
    r = _get_redis_client()

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }

    if sources:
        message["sources"] = sources

    r.rpush(f"chat:{conversation_id}", json.dumps(message))

    # safer update
    r.hincrby(f"conversation:{conversation_id}", "message_count", 1)

    r.hset(f"conversation:{conversation_id}", mapping={
        "updated_at": datetime.utcnow().isoformat()
    })


def get_chat_history(conversation_id: str, limit: int = 20) -> List[Dict]:
    r = _get_redis_client()

    raw = r.lrange(f"chat:{conversation_id}", -limit, -1)
    return [json.loads(m) for m in raw]


def clear_chat(conversation_id: str):
    r = _get_redis_client()

    r.delete(f"chat:{conversation_id}")

    r.hset(f"conversation:{conversation_id}", mapping={
        "message_count": "0",
        "updated_at": datetime.utcnow().isoformat()
    })