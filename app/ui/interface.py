import os
import tempfile
from pathlib import Path
from typing import Any, List, Dict, Optional

import gradio as gr
import httpx

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CUSTOM_CSS = """
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap");

:root{
    --bg:#eaf6ee;
    --bg-soft:#d8ecde;
    --panel:#ffffff;
    --panel-soft:#f5fbf7;
    --border:#b9d9c2;
    --border-strong:#7fbd93;
    --text:#163325;
    --heading:#0e2a1d;
    --muted:#446a53;
    --input-bg:#ffffff;
    --input-text:#1a2f24;
    --accent:#39bf77;
    --accent-strong:#229958;
    --accent-soft:#e7f6ec;
    --warning:#f5b84b;
    --shadow:0 10px 28px rgba(21,63,39,0.12);
    --shadow-soft:0 4px 16px rgba(21,63,39,0.08);
    --radius:8px;
    --footer-border:#cde4d5;
}
body.light,
.light,
.gradio-container.light{
    --bg:#eaf6ee;
    --bg-soft:#d8ecde;
    --panel:#ffffff;
    --panel-soft:#f5fbf7;
    --border:#b9d9c2;
    --border-strong:#7fbd93;
    --text:#163325;
    --heading:#0e2a1d;
    --muted:#446a53;
    --input-bg:#ffffff;
    --input-text:#1a2f24;
    --accent:#39bf77;
    --accent-strong:#229958;
    --accent-soft:#e7f6ec;
    --warning:#f5b84b;
    --shadow:0 10px 28px rgba(21,63,39,0.12);
    --shadow-soft:0 4px 16px rgba(21,63,39,0.08);
    --radius:8px;
    --footer-border:#cde4d5;
}
body.dark,
.dark,
.gradio-container.dark{
    --bg:#07170f;
    --bg-soft:#0c2419;
    --panel:#102b1f;
    --panel-soft:#153426;
    --border:#2f6c50;
    --border-strong:#47d68a;
    --text:#edf8f1;
    --heading:#f6fff9;
    --muted:#b8d7c6;
    --input-bg:#0d2319;
    --input-text:#edf8f1;
    --accent:#47d68a;
    --accent-strong:#1fa85d;
    --accent-soft:#1f4f39;
    --warning:#f9cf65;
    --shadow:0 14px 32px rgba(3,10,7,0.30);
    --shadow-soft:0 6px 18px rgba(3,10,7,0.22);
    --radius:8px;
    --footer-border:#2f6c50;
}
@media (prefers-color-scheme: dark){
    :root{
        --bg:#07170f;
        --bg-soft:#0c2419;
        --panel:#102b1f;
        --panel-soft:#153426;
        --border:#2f6c50;
        --border-strong:#47d68a;
        --text:#edf8f1;
        --heading:#f6fff9;
        --muted:#b8d7c6;
        --input-bg:#0d2319;
        --input-text:#edf8f1;
        --accent:#47d68a;
        --accent-strong:#1fa85d;
        --accent-soft:#1f4f39;
        --warning:#f9cf65;
        --shadow:0 14px 32px rgba(3,10,7,0.30);
        --shadow-soft:0 6px 18px rgba(3,10,7,0.22);
        --radius:8px;
        --footer-border:#2f6c50;
    }
}
*{
    box-sizing:border-box;
}
body,
.gradio-container{
    background:
        radial-gradient(circle at 12% 6%,rgba(71,214,138,0.16),transparent 34%),
        radial-gradient(circle at 87% 4%,rgba(69,190,119,0.10),transparent 31%),
        linear-gradient(155deg,var(--bg) 0%,var(--bg-soft) 56%,var(--bg) 100%) !important;
    color:var(--text);
    font-family:"IBM Plex Sans","Noto Sans",sans-serif;
    font-size:16px;
    line-height:1.5;
}
.app-shell{
    max-width:1460px;
    margin:0 auto;
    padding:18px;
}
.topbar{
    align-items:center;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:var(--radius);
    box-shadow:var(--shadow);
    margin-bottom:16px;
    padding:18px 20px;
}
.brand-title h2{
    color:var(--heading);
    font-size:1.62rem;
    line-height:1.2;
    margin:0 0 6px;
}
.brand-title p{
    color:var(--muted);
    font-size:0.97rem;
    margin:0;
}
.panel{
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:var(--radius);
    box-shadow:var(--shadow-soft);
    padding:16px;
}
.rail{
    min-width:230px;
    position:sticky;
    top:14px;
}
.right-rail{
    min-width:300px;
}
.section-title h3{
    color:var(--heading);
    font-size:1rem;
    letter-spacing:0;
    margin:4px 0 8px;
}
.hint,
.hint p{
    color:var(--muted);
    font-size:0.94rem;
    line-height:1.48;
    margin:0;
}
.status-card textarea,
.status-card input{
    font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
    font-size:0.86rem !important;
}
.workspace{
    align-items:flex-start;
    gap:16px;
}
.doc-heading{
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:var(--radius);
    box-shadow:var(--shadow-soft);
    padding:12px 14px;
}
.doc-heading h3{
    color:var(--heading);
    margin:0;
}
.status-badge{
    align-items:center;
    background:var(--accent-soft);
    border:1px solid var(--border-strong);
    border-radius:999px;
    color:var(--heading);
    display:inline-flex;
    font-size:0.78rem;
    font-weight:700;
    margin-left:8px;
    padding:3px 9px;
}
.chat-panel{
    padding:0;
}
.chat-panel .wrap{
    background:var(--panel) !important;
    border:1px solid var(--border) !important;
    border-radius:var(--radius) !important;
    box-shadow:var(--shadow-soft);
}
.chat-panel .message-wrap,
.chat-panel .message{
    font-size:1rem;
    line-height:1.58;
}
.composer{
    align-items:stretch;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:var(--radius);
    box-shadow:var(--shadow-soft);
    gap:10px;
    padding:11px;
}
.actions-row{
    display:flex;
    flex-wrap:wrap;
    gap:9px;
}
.main-actions{
    gap:10px;
}
.gradio-container label,
.gradio-container .block-title,
.gradio-container .prose h1,
.gradio-container .prose h2,
.gradio-container .prose h3{
    color:var(--heading) !important;
    font-weight:620 !important;
}
.gradio-container textarea,
.gradio-container input,
.gradio-container select{
    background:var(--input-bg) !important;
    border:1px solid var(--border) !important;
    border-radius:var(--radius) !important;
    color:var(--input-text) !important;
}
.gradio-container textarea::placeholder,
.gradio-container input::placeholder{
    color:#9ec7b2 !important;
    opacity:0.95;
}
.gradio-container textarea:focus,
.gradio-container input:focus,
.gradio-container select:focus{
    border-color:var(--accent) !important;
    box-shadow:0 0 0 2px rgba(71,214,138,0.28) !important;
    outline:none !important;
}
.quick-btn button,
.primary-btn button,
.secondary-btn button{
    border-radius:var(--radius) !important;
    font-size:0.97rem !important;
    font-weight:650 !important;
    min-height:44px;
    transition:all 0.18s ease;
}
.primary-btn button{
    background:linear-gradient(180deg,var(--accent) 0%,var(--accent-strong) 100%) !important;
    border:1px solid rgba(14,57,34,0.8) !important;
    color:#042210 !important;
}
.secondary-btn button{
    background:var(--accent-soft) !important;
    border:1px solid var(--border) !important;
    color:var(--text) !important;
}
.quick-btn button{
    background:var(--panel-soft) !important;
    border:1px solid var(--border) !important;
    color:var(--text) !important;
    min-width:155px;
}
.service-btn button,
.session-btn button{
    width:100%;
}
.quick-btn button:hover,
.primary-btn button:hover,
.secondary-btn button:hover{
    filter:brightness(1.06);
    transform:translateY(-1px);
}
.quick-btn button:active,
.primary-btn button:active,
.secondary-btn button:active{
    transform:translateY(0);
}
.gradio-container .block,
.gradio-container .form{
    border-color:var(--border) !important;
}
.gradio-container .file-preview,
.gradio-container .file-preview-holder{
    background:var(--input-bg) !important;
    border-color:var(--border) !important;
    color:var(--input-text) !important;
}
.chat-input textarea{
    min-height:60px !important;
}
.preview-wrap{
    overflow:hidden;
}
.preview-wrap img{
    background:var(--panel-soft);
    border-radius:var(--radius);
    object-fit:contain;
}
.preview-wrap .wrap{
    background:var(--input-bg) !important;
    border-color:var(--border) !important;
}
::-webkit-scrollbar{
    width:10px;
    height:10px;
}
::-webkit-scrollbar-thumb{
    background:var(--border-strong);
    border-radius:999px;
}
footer{
    display:block !important;
    margin-top:18px !important;
    padding:12px 0 8px !important;
    border-top:1px solid var(--footer-border) !important;
}
footer *{
    color:var(--muted) !important;
}
footer a{
    color:var(--accent-strong) !important;
}
@media (max-width: 1200px){
    .app-shell{padding:14px}
    .topbar{padding:14px}
    .rail{position:static}
}
@media (max-width: 900px){
    .rail{min-width:0}
    .right-rail{min-width:0}
    .actions-row{gap:8px}
    .quick-btn button{min-width:100%}
    .composer{padding:9px}
    .brand-title h2{font-size:1.38rem}
}
"""


def _format_citations(citations: List[dict]) -> str:
    if not citations:
        return ""
    lines = ["Sources:"]
    for item in citations:
        source = item.get("source", "unknown")
        section = item.get("section", "N/A")
        lines.append(f"- {source} ({section})")
    return "\n".join(lines)


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except Exception:
        return response.text


def _welcome_message(has_docs: bool = False) -> List[dict[str, str]]:
    if has_docs:
        text = (
            "Documents are indexed and ready.\n\n"
            "Ask a contract question, request a summary, or use a quick action below."
        )
    else:
        text = (
            "Upload a contract to begin.\n\n"
            "Once indexing finishes, I can answer questions with source citations."
        )
    return [{"role": "assistant", "content": text}]


def _document_title(file_name: str | None) -> str:
    if not file_name:
        return "### No document selected"
    return f"### {file_name} <span class='status-badge'>Processed</span>"


def _generate_pdf_preview(pdf_path: str) -> Optional[str]:
    """Render the first page of a PDF to a PNG and return the temp path."""
    if not fitz:
        return None
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        pix.save(tmp_path)
        doc.close()
        return tmp_path
    except Exception:
        return None


def select_document(selected: str, session: dict | None):
    """Update the UI to show the selected document and a preview if available."""
    if not selected:
        return (
            gr.update(value="### No document selected"),
            gr.update(value=None),
            gr.update(value=None),
            "No document selected.",
        )

    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    candidate = upload_dir / selected
    title_html = _document_title(selected)
    preview_img = None
    preview_file_value = None
    if candidate.exists():
        preview_file_value = str(candidate)
        if candidate.suffix.lower() == ".pdf":
            preview_img = _generate_pdf_preview(str(candidate))

    if preview_img:
        status_text = "Document selected. Preview loaded."
    elif preview_file_value:
        status_text = "Document selected. Preview is available for PDF files."
    else:
        status_text = "Document selected, but the local file could not be found."
    return (
        gr.update(value=title_html),
        gr.update(value=preview_img),
        gr.update(value=preview_file_value),
        status_text,
    )


def check_api_health() -> str:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        return f"API status: Offline\nDetails: {exc}"

    readiness = "Ready" if data.get("services_ready") else "Running (documents not initialized yet)"
    return f"API status: Online\nService state: {readiness}"


def upload_files(files: List[gr.File], session: dict | None):
    session = session or {"has_docs": False, "files": []}
    if not files:
        return (
            "Please upload at least one .pdf or .docx file.",
            session,
            "Step 1 of 2: Upload a contract file to begin.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "No files uploaded yet.",
            gr.update(choices=session.get("files", []), value=None),
            gr.update(value=_document_title(None)),
            gr.update(value=None),
            gr.update(value=None),
        )

    prepared = []
    for f in files:
        file_path = Path(f.name)
        prepared.append(("files", (file_path.name, open(file_path, "rb"), "application/octet-stream")))

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{API_BASE_URL}/upload", files=prepared)
            response.raise_for_status()
            data = response.json()
            uploaded_files = data.get("files", [])
            session = {"has_docs": True, "files": uploaded_files}
            # prepare document selector + preview for first uploaded file
            selected = uploaded_files[0] if uploaded_files else None
            upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
            preview_img = None
            preview_file_value = None
            title_html = _document_title(None)
            if selected:
                candidate = upload_dir / selected
                title_html = _document_title(selected)
                if candidate.exists() and candidate.suffix.lower() == ".pdf":
                    preview_img = _generate_pdf_preview(str(candidate))
                    preview_file_value = str(candidate)

            return (
                f"{data.get('message')}\nFiles: {', '.join(uploaded_files)}",
                session,
                "Step 2 of 2: Ask a question in chat. You can also click 'Summarize Contract'.",
                _welcome_message(True),
                _welcome_message(True),
                "Documents indexed successfully. You are ready to chat.",
                gr.update(choices=uploaded_files, value=selected),
                gr.update(value=title_html),
                gr.update(value=preview_img),
                gr.update(value=preview_file_value),
            )
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        suffix = f" - {detail}" if detail else ""
        return (
            f"Upload failed ({exc.response.status_code} {exc.response.reason_phrase}){suffix}",
            session,
            "Upload failed. Please verify file type/contents and try again.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "Upload failed. The assistant is not ready yet.",
            gr.update(choices=session.get("files", []), value=None),
            gr.update(value=_document_title(None)),
            gr.update(value=None),
            gr.update(value=None),
        )
    except Exception as exc:
        return (
            f"Upload failed: {exc}",
            session,
            "Upload failed due to a local/network issue. Retry after checking API health.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "Upload failed. The assistant is not ready yet.",
            gr.update(choices=session.get("files", []), value=None),
            gr.update(value=_document_title(None)),
            gr.update(value=None),
            gr.update(value=None),
        )
    finally:
        for _, (_, file_obj, _) in prepared:
            try:
                file_obj.close()
            except Exception:
                pass


def ask_question(message: str, history: List[dict[str, Any]], session: dict | None):
    history = history or _welcome_message((session or {}).get("has_docs", False))
    message = (message or "").strip()
    if not message:
        return history, history, "", "Type a question to continue."
    if not (session or {}).get("has_docs"):
        history.append({"role": "user", "content": message})
        history.append(
            {
                "role": "assistant",
                "content": (
                    "I don't have any indexed contract yet. "
                    "Please upload a PDF or DOCX file first from the right panel."
                ),
            }
        )
        return history, history, "", "Upload at least one document before asking questions."
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{API_BASE_URL}/ask", json={"question": message})
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_detail(exc.response)
        assistant_reply = (
            f"Request failed ({exc.response.status_code} {exc.response.reason_phrase}): {detail}"
        )
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history, "", "Question request failed. Check API health and try again."
    except Exception as exc:
        assistant_reply = f"Request failed: {exc}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history, "", "Question request failed. Check connection and retry."

    answer = data.get("answer", "")
    citations = _format_citations(data.get("citations", []))
    full_answer = answer if not citations else f"{answer}\n\n{citations}"

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": full_answer})
    return history, history, "", "Answer generated successfully."


def summarize_contract(history: List[dict[str, Any]], session: dict | None):
    history = history or _welcome_message((session or {}).get("has_docs", False))
    prompt = "Summarize the uploaded contract"
    if not (session or {}).get("has_docs"):
        history.append({"role": "user", "content": prompt})
        history.append(
            {
                "role": "assistant",
                "content": "Please upload a contract first, then I can provide an executive summary.",
            }
        )
        return history, history, "Upload a contract first to use summarize."
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{API_BASE_URL}/summary")
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_detail(exc.response)
        assistant_reply = (
            f"Summary failed ({exc.response.status_code} {exc.response.reason_phrase}): {detail}"
        )
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history, "Summary failed. Check API health and retry."
    except Exception as exc:
        assistant_reply = f"Summary failed: {exc}"
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history, "Summary failed due to connection/runtime issue."

    answer = data.get("answer", "")
    citations = _format_citations(data.get("citations", []))
    full_answer = answer if not citations else f"{answer}\n\n{citations}"
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": full_answer})
    return history, history, "Summary generated successfully."


def clear_conversation(session: dict | None):
    has_docs = (session or {}).get("has_docs", False)
    fresh = _welcome_message(has_docs)
    status_text = "Chat cleared. Documents are still indexed and ready." if has_docs else "Chat cleared."
    return fresh, fresh, status_text


def use_quick_prompt(prompt: str, history: List[dict[str, Any]], session: dict | None):
    return ask_question(prompt, history, session)


def quick_payment_terms(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("Summarize the payment terms and due dates.", history, session)


def quick_termination(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("Explain the termination clause and notice periods.", history, session)


def quick_risks(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("Identify potentially risky or one-sided clauses.", history, session)


def download_summary(session: dict | None):
    if not (session or {}).get("has_docs"):
        return "No indexed documents to summarize.", None
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{API_BASE_URL}/summary")
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_detail(exc.response)
        return f"Summary failed ({exc.response.status_code}): {detail}", None
    except Exception as exc:
        return f"Summary failed: {exc}", None

    answer = data.get("answer", "")
    citations = _format_citations(data.get("citations", []))
    full_answer = answer if not citations else f"{answer}\n\n{citations}"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write(full_answer.encode("utf-8"))
    tmp.flush()
    tmp.close()
    return "Summary ready for download.", tmp.name


def export_chat(history: List[dict[str, Any]]):
    if not history:
        return "No conversation to export.", None
    lines = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        lines.append(f"{role.upper()}:\n{content}\n\n")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write("\n".join(lines).encode("utf-8"))
    tmp.flush()
    tmp.close()
    return "Chat exported.", tmp.name


with gr.Blocks(
    title="Smart Contract Assistant",
    fill_width=True,
) as demo:
    with gr.Column(elem_classes=["app-shell"]):
        with gr.Row(elem_classes=["topbar"]):
            with gr.Column(scale=12, elem_classes=["brand-title"]):
                gr.Markdown(
                    """
## Smart Contract Assistant
Upload agreements, ask direct questions, and get citation-backed answers.
"""
                )

        memory_state = gr.State(_welcome_message(False))
        session_state = gr.State({"has_docs": False, "files": []})

        with gr.Row(elem_classes=["workspace"]):
            with gr.Column(scale=2, elem_classes=["panel", "rail"]):
                gr.Markdown("### Workspace", elem_classes=["section-title"])
                gr.Markdown(
                    "Select an indexed document to preview it, then use the chat to inspect clauses.",
                    elem_classes=["hint"],
                )
                document_selector = gr.Dropdown(
                    choices=[],
                    label="Indexed Documents",
                    value=None,
                    interactive=True,
                )
                assistant_status = gr.Textbox(
                    label="Assistant Status",
                    value="No files uploaded yet.",
                    interactive=False,
                    lines=4,
                )
                gr.Markdown("### Session", elem_classes=["section-title"])
                clear_button = gr.Button("Clear Chat", elem_classes=["secondary-btn", "session-btn"])
                export_button = gr.Button("Export Chat", elem_classes=["secondary-btn", "session-btn"])
                export_file = gr.File(visible=False)
                gr.Markdown("### Service", elem_classes=["section-title"])
                with gr.Column(elem_classes=["status-card"]):
                    health_button = gr.Button("Check API Health", elem_classes=["secondary-btn", "service-btn"])
                    health_status = gr.Textbox(
                        label="API Health",
                        value="API status: Not checked",
                        interactive=False,
                        lines=2,
                    )
         
            with gr.Column(scale=6):
                doc_title = gr.Markdown(_document_title(None), elem_classes=["doc-heading"])
                with gr.Row(elem_classes=["chat-panel"]):
                    chatbot = gr.Chatbot(
                        value=_welcome_message(False),
                        height=600,
                        label="Contract Chat",
                        layout="bubble",
                        buttons=["copy", "copy_all"],
                        placeholder="Upload a contract to begin.",
                    )
                with gr.Row(elem_classes=["composer"]):
                    user_message = gr.Textbox(
                        show_label=False,
                        placeholder="Ask about payment terms, termination, obligations, risks...",
                        lines=2,
                        max_lines=4,
                        scale=8,
                        autofocus=True,
                        elem_classes=["chat-input"],
                    )
                    send_btn = gr.Button("Send", scale=1, elem_classes=["primary-btn"])
                with gr.Row(elem_classes=["actions-row"]):
                    quick_btn_1 = gr.Button("Payment Terms", elem_classes=["quick-btn"])
                    quick_btn_2 = gr.Button("Termination Clause", elem_classes=["quick-btn"])
                    quick_btn_3 = gr.Button("Risky Clauses", elem_classes=["quick-btn"])
                with gr.Row(elem_classes=["main-actions"]):
                    summary_button = gr.Button("Summarize Contract", elem_classes=["primary-btn"])
                    summary_download_button = gr.Button(
                        "Download Latest Summary",
                        elem_classes=["secondary-btn"],
                    )
                    summary_file = gr.File(visible=False)

            with gr.Column(scale=4, elem_classes=["right-rail"]):
                with gr.Column(elem_classes=["panel"]):
                    gr.Markdown("### Upload Documents", elem_classes=["section-title"])
                    gr.Markdown(
                        "Drag and drop PDF or DOCX files, then index them for chat.",
                        elem_classes=["hint"],
                    )
                    uploader = gr.File(
                        label="PDF or DOCX files",
                        file_count="multiple",
                        file_types=[".pdf", ".docx"],
                    )
                    upload_button = gr.Button("Upload and Index", elem_classes=["primary-btn"])
                    upload_status = gr.Textbox(
                        label="Upload Status",
                        value="No upload yet.",
                        interactive=False,
                        lines=3,
                    )

                with gr.Column(elem_classes=["panel", "preview-wrap"]):
                    gr.Markdown("### Document Preview", elem_classes=["section-title"])
                    doc_preview = gr.Image(
                        value=None,
                        label="First page preview",
                        height=360,
                        type="filepath",
                        buttons=["download", "fullscreen"],
                        placeholder="Preview appears after a PDF is uploaded.",
                    )
                    preview_file = gr.File(visible=False)

    # Wire up interactions
    upload_button.click(
        upload_files,
        inputs=[uploader, session_state],
        outputs=[
            upload_status,
            session_state,
            memory_state,
            chatbot,
            memory_state,
            assistant_status,
            document_selector,
            doc_title,
            doc_preview,
            preview_file,
        ],
    )

    # Update preview when a document is selected from the sidebar
    document_selector.change(
        select_document,
        inputs=[document_selector, session_state],
        outputs=[doc_title, doc_preview, preview_file, assistant_status],
    )

    health_button.click(check_api_health, outputs=[health_status])
    chat_outputs = [chatbot, memory_state, user_message, assistant_status]
    send_btn.click(
        ask_question,
        inputs=[user_message, memory_state, session_state],
        outputs=chat_outputs,
    )
    user_message.submit(
        ask_question,
        inputs=[user_message, memory_state, session_state],
        outputs=chat_outputs,
    )
    summary_button.click(summarize_contract, inputs=[memory_state, session_state], outputs=[chatbot, memory_state, assistant_status])
    clear_button.click(clear_conversation, inputs=[session_state], outputs=[chatbot, memory_state, assistant_status])
    quick_btn_1.click(quick_payment_terms, inputs=[memory_state, session_state], outputs=[chatbot, memory_state, user_message, assistant_status])
    quick_btn_2.click(quick_termination, inputs=[memory_state, session_state], outputs=[chatbot, memory_state, user_message, assistant_status])
    quick_btn_3.click(quick_risks, inputs=[memory_state, session_state], outputs=[chatbot, memory_state, user_message, assistant_status])

    summary_download_button.click(download_summary, inputs=[session_state], outputs=[assistant_status, summary_file])
    export_button.click(export_chat, inputs=[memory_state], outputs=[assistant_status, export_file])


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS,
    )
