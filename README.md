# Smart Contract Assistant

A local Retrieval-Augmented Generation (RAG) assistant for contract analysis.

It lets you:
- Upload contract files (`.pdf`, `.docx`)
- Ask questions grounded in the uploaded documents
- Generate executive summaries with source citations

## Project Overview

This project has two main apps:
- **FastAPI backend**: document ingestion, vector indexing (Chroma), RAG endpoints
- **Gradio frontend**: chat-style UI for upload, Q&A, and summaries

Core stack:
- FastAPI + Uvicorn
- LangChain + ChromaDB
- SentenceTransformers embeddings (with deterministic fake-embedding fallback)
- Ollama (`ChatOllama`) for local LLM inference
- Gradio for UI

## Folder Structure

```text
app/
  api/server.py         # FastAPI app and endpoints
  core/ingestion.py     # PDF/DOCX loading, chunking, vectorstore management
  core/rag_chain.py     # Retrieval + LLM chains, guardrails, citations
  ui/interface.py       # Gradio frontend
uploads/                # Uploaded contract files
chroma_db/              # Persistent Chroma vector DB
main.py                 # Exposes FastAPI app import
requirements.txt
```

## Prerequisites

- Python 3.10+
- Ollama installed and running locally
- At least one local Ollama model pulled (default expects `llama3.2:latest`)

Example:

```powershell
ollama pull llama3.2
ollama serve
```

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the Backend API

```powershell
uvicorn app.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Backend base URL: `http://127.0.0.1:8000`

Useful endpoint:
- `GET /health`

## Running the Gradio UI

In a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python app\ui\interface.py
```

Frontend URL: `http://127.0.0.1:7860`

## API Endpoints

- `GET /health`
  - Returns service status and whether documents are initialized.

- `POST /upload`
  - Multipart form field: `files` (one or more `.pdf` / `.docx` files)
  - Clears previous vector index, ingests new documents, and refreshes retriever.

- `POST /ask`
  - JSON body:
    ```json
    { "question": "What are the payment terms?" }
    ```
  - Returns answer plus citations.

- `POST /summary`
  - Returns high-level executive summary plus citations.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `UPLOAD_DIR` | `./uploads` | Upload storage directory |
| `CHROMA_PATH` | `./chroma_db` | Chroma persistence path |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:latest` | Preferred Ollama model |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL used by Gradio UI |
| `USE_FAKE_EMBEDDINGS` | `0` | Set `1` to use deterministic fake embeddings |
| `ENABLE_LANGSERVE_ROUTES` | `0` | Set `1` to expose optional `/rag` and `/summary_chain` LangServe routes |

## Notes on Behavior

- Uploading new documents replaces the previous indexed set.
- The assistant includes scope guardrails and only answers from uploaded contract context.
- Greeting prompts are handled directly (for better UX) before retrieval.
- If embedding model download is blocked, the app falls back to fake embeddings to keep local development runnable.

## Troubleshooting

- **`/health` is online but answers fail**:
  - Ensure Ollama is running and the selected model exists.

- **No meaningful retrieval results**:
  - Confirm your documents contain extractable text (not image-only scans).

- **UI cannot connect to API**:
  - Verify backend is running on `127.0.0.1:8000` or set `API_BASE_URL` accordingly.

## License

No license file is currently defined in this repository.