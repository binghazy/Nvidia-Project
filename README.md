# NVIDIA RAG Project

A Retrieval-Augmented Generation (RAG) application that allows users to upload documents (PDF, DOCX) and ask questions about them using AI-powered insights. The system uses Ollama for local LLM processing and Chroma DB for vector storage.

## Features

- **Document Processing**: Upload and process PDF and DOCX files
- **RAG Chain**: Retrieval-Augmented Generation for accurate document-based Q&A
- **Local LLM**: Uses Ollama (llama3.2) for on-device processing
- **Vector Database**: Chroma DB for efficient document embeddings and retrieval
- **Web Interface**: Gradio-based UI for easy interaction
- **API Server**: FastAPI backend for programmatic access
- **Smart Guardrails**: Ensures responses stay relevant to uploaded documents

## Demo Video

Watch the project in action:

[![Video Demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://drive.google.com/file/d/1S5PF5tQSHnEwnMPX72-r4bTdwXcmML3U/view?usp=sharing)

[Full Video Link](https://drive.google.com/file/d/1S5PF5tQSHnEwnMPX72-r4bTdwXcmML3U/view?usp=sharing)

## Project Structure

```
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── app/
│   ├── api/
│   │   └── server.py      # FastAPI server
│   ├── core/
│   │   ├── ingestion.py   # Document processing
│   │   └── rag_chain.py   # RAG logic
│   └── ui/
│       └── interface.py   # Gradio UI
├── chroma_db/             # Vector database storage
└── uploads/               # Uploaded documents
```

## Requirements

- Python 3.8+
- Ollama (running on localhost:11434)
- 8GB+ RAM recommended

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Nividia-Project-main
   ```

2. **Create virtual environment** (optional but recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install and run Ollama**
   - Download from [ollama.ai](https://ollama.ai)
   - Run: `ollama serve`
   - Pull the model: `ollama pull llama3.2`

## Usage

### Start the Gradio Interface

```bash
python app/ui/interface.py
```

This launches the web UI where you can upload documents and ask questions.

### Start the FastAPI Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

## How It Works

1. **Document Upload**: Users upload PDF or DOCX files
2. **Processing**: Documents are split into chunks and processed
3. **Embedding**: Text chunks are converted to embeddings using Sentence Transformers
4. **Storage**: Embeddings are stored in Chroma DB for fast retrieval
5. **Query**: When a question is asked, relevant document chunks are retrieved
6. **Generation**: The LLM generates an answer using retrieved context
7. **Response**: Answer is returned with guardrails to ensure relevance

## Configuration

Set environment variables to customize behavior:

- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama3.2:latest)

## Dependencies

- **LangChain**: RAG chain orchestration
- **FastAPI**: API framework
- **Gradio**: Web interface
- **Chroma DB**: Vector database
- **Sentence Transformers**: Embeddings
- **Ollama**: Local LLM inference
- **PyMuPDF**: PDF processing
- **python-docx**: DOCX processing

## Troubleshooting

- **Connection Error**: Make sure Ollama is running on localhost:11434
- **Out of Memory**: Reduce chunk size or use a smaller model
- **Slow Responses**: Check Ollama model is fully loaded

## License

MIT

## Contributing

Feel free to submit issues and enhancement requests!
