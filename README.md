# RepoChat - Talk to Any Codebase

Transform any GitHub repository into an AI-powered chatbot. Ask questions, explore code, and understand complex projects in seconds.

## What is RepoChat?

Stop struggling to understand unfamiliar codebases. RepoChat uses AI and semantic search to answer questions about any GitHub repository - instantly.

### The Problem
- Onboarding to new projects takes days
- Reading thousands of lines of code to find one function
- Documentation is outdated or missing
- No way to ask questions about legacy code

### The Solution

RepoChat turns entire repositories into conversational AI assistants.

Simply paste a GitHub URL, and within minutes you can:
- Ask "How does authentication work?" and get exact file/line references
- Query "Where is the payment logic?" and see all relevant code
- Explore "Explain the database schema" and understand architecture instantly
- Debug "What handles user sessions?" and find the code that matters

No more Ctrl+F. No more endless file browsing. Just ask.

---

## Key Features

- Process entire repositories - No file limits, handles 1000+ file projects
- Semantic code search - Finds relevant code by meaning, not just keywords
- Natural language Q&A - Ask questions like you would to a senior developer
- Precise citations - Every answer includes exact file paths and line numbers
- Multiple conversations - Organize different topics in separate chat threads
- Real-time streaming - See AI responses as they're generated
- 100% Free - Uses Groq API (14,400 free requests/day) + local embeddings

---

## Architecture

RepoChat uses RAG (Retrieval-Augmented Generation) to provide accurate, context-aware answers:
```
GitHub Repo → Clone → Chunk Code → Create Embeddings → Vector Database
                                                              ↓
User Question → Semantic Search → Find Relevant Code → LLM → Answer
```

### Tech Stack

**Backend:**
- FastAPI - High-performance Python web framework
- Groq API - Lightning-fast LLM inference (Llama 3.3 70B)
- ChromaDB - Vector database for semantic code search
- Sentence Transformers - Local embedding generation (free)
- Redis - Chat history and session management

**Frontend:**
- Next.js 14 - React framework
- Tailwind CSS - Styling
- TypeScript - Type safety

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+
- Redis
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/a2yshh/repochat.git
cd repochat
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your Groq API key from https://console.groq.com/keys

# Start Redis
docker run -d -p 6380:6379 --name repochat-redis redis:latest

# Run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### 4. Open App

Go to `http://localhost:3000`

---

## Usage

1. Paste GitHub URL: `https://github.com/facebook/react`
2. Wait 1-2 minutes for processing
3. Ask questions about the code
4. Get answers with exact file/line references

---

## Use Cases

- **Developer Onboarding** - New hires understand codebase instantly
- **Code Review** - Ask "What does this change affect?" to see related code
- **Legacy Code Exploration** - Understand old projects without reading everything
- **Open Source Learning** - Learn how popular projects work
- **Documentation** - Generate comprehensive overviews quickly

---

## Performance

- Processing: 1-2 minutes for 100-file repo
- Query response: 0.5-2 seconds (streaming)
- Embedding model: 90MB (downloads once)
- Memory usage: ~1GB RAM during processing

---

