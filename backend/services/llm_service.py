import os
from typing import List, AsyncGenerator

from groq import Groq, AsyncGroq
from services.redis_service import get_chat_history, add_message

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


def _get_client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def _get_async_client() -> AsyncGroq:
    return AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


def _build_prompt(query: str, context_chunks: List[dict]) -> str:
    formatted_chunks = []
    for i, chunk in enumerate(context_chunks, 1):
        formatted_chunks.append(
            f"--- Source {i}: {chunk['file_path']} "
            f"(lines {chunk['start_line']}-{chunk['end_line']}) ---\n"
            f"```{chunk.get('language', '')}\n{chunk['content']}\n```"
        )

    context = "\n\n".join(formatted_chunks)

    return f"""You are a knowledgeable code assistant. Answer the question using ONLY the provided code context from the repository. If the answer cannot be determined from the context, say so clearly.

FORMATTING RULES (important):
- Use proper Markdown formatting for readability
- Use headings (##, ###) to organize sections
- Use bullet points or numbered lists for multiple items
- Use **bold** for emphasis on key terms
- Use `inline code` for file names, function names, variables
- Use fenced code blocks with language tags for code snippets:
```javascript
  // code here
```
- Keep paragraphs short and well-spaced
- Reference files as `filename.ext:line_number` format

Code Context:
{context}

Question: {query}

Provide a well-formatted, organized answer with clear structure and specific code references."""


def generate_response(conversation_id: str, query: str, context_chunks: List[dict]) -> str:
    client = _get_client()
    prompt = _build_prompt(query, context_chunks)
    history = get_chat_history(conversation_id)
    messages = history + [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )

    answer = response.choices[0].message.content
    sources = [chunk['file_path'] for chunk in context_chunks]
    add_message(conversation_id, "user", query)
    add_message(conversation_id, "assistant", answer, sources)
    return answer


async def generate_response_stream(
    conversation_id: str, query: str, context_chunks: List[dict]
) -> AsyncGenerator[str, None]:
    client = _get_async_client()
    prompt = _build_prompt(query, context_chunks)
    history = get_chat_history(conversation_id)
    messages = history + [{"role": "user", "content": prompt}]

    stream = await client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
        stream=True,
    )
    full_answer = ""

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_answer += text
            yield text

    sources = [chunk['file_path'] for chunk in context_chunks]
    add_message(conversation_id, "user", query)
    add_message(conversation_id, "assistant", full_answer, sources)