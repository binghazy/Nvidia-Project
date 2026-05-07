import os
from pathlib import Path
from typing import Any, List

import gradio as gr
import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

:root {
  --bg-soft: #f2f6fb;
  --panel-bg: #ffffff;
  --text-main: #0f172a;
  --text-subtle: #475569;
  --line: #d8e2ee;
  --accent: #0ea5e9;
  --accent-strong: #0284c7;
}

html, body, .gradio-container {
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  font-family: "Manrope", sans-serif !important;
  color: var(--text-main) !important;
  background: var(--bg-soft) !important;
}

.gradio-container {
  padding: 0 !important;
}

.app-shell {
  max-width: 1220px !important;
  margin: 0 auto !important;
  padding: 12px !important;
}

.hero {
  padding: 8px 4px 10px 4px !important;
}

.hero h1 {
  margin: 0 !important;
  font-size: 1.55rem !important;
  line-height: 1.2 !important;
  letter-spacing: -0.02em !important;
}

.hero p {
  margin: 4px 0 0 0 !important;
  color: var(--text-subtle) !important;
  font-size: 0.9rem !important;
}

.card {
  background: var(--panel-bg) !important;
  border: 1px solid var(--line) !important;
  border-radius: 14px !important;
  padding: 12px !important;
}

.gr-chatbot {
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  min-height: 480px !important;
}

.gr-button-primary {
  background: linear-gradient(90deg, var(--accent), var(--accent-strong)) !important;
  border: none !important;
  font-size: 0.88rem !important;
}

.composer-shell {
  margin-top: 10px !important;
  padding: 9px 10px !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 12px !important;
  background: #ffffff !important;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
}

#chat-composer {
  margin-bottom: 0 !important;
}

#chat-composer textarea {
  border: none !important;
  box-shadow: none !important;
  padding: 4px 4px !important;
  font-size: 0.9rem !important;
  line-height: 1.3 !important;
  min-height: 30px !important;
  max-height: 70px !important;
}

#chat-composer textarea:focus {
  border: none !important;
  box-shadow: none !important;
}

.quick-actions {
  margin: 8px 0 0 0 !important;
  gap: 4px !important;
}

.quick-actions button {
  padding: 4px 8px !important;
  font-size: 0.8rem !important;
}

.row {
  gap: 10px !important;
  margin: 0 !important;
}

.column {
  padding: 0 !important;
  margin: 0 !important;
}

@media (max-width: 900px) {
  .gr-chatbot {
    min-height: 360px !important;
  }
}
"""


def _default_session() -> dict:
    return {"has_docs": False, "files": []}


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
            "Documents indexed successfully.\n\n"
            "Ask questions about clauses, obligations, payment terms, dates, and risks."
        )
    else:
        text = (
            "Welcome.\n\n"
            "1) Upload PDF or DOCX files.\n"
            "2) Wait for indexing.\n"
            "3) Ask contract questions in chat."
        )
    return [{"role": "assistant", "content": text}]


def _files_table(file_names: List[str]) -> List[List[str]]:
    return [[name] for name in file_names]


def _normalize_history(history: Any, has_docs: bool) -> List[dict[str, str]]:
    if isinstance(history, list):
        return history
    return _welcome_message(has_docs)


def check_api_health() -> str:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        return f"API: Offline | {exc}"

    readiness = "Ready" if data.get("services_ready") else "Running (documents not initialized yet)"
    return f"API: Online | State: {readiness}"


def _resolve_uploaded_path(file_item: Any) -> Path:
    if isinstance(file_item, (str, os.PathLike)):
        return Path(file_item)

    name = getattr(file_item, "name", None)
    if isinstance(name, str) and name.strip():
        return Path(name)

    path = getattr(file_item, "path", None)
    if isinstance(path, str) and path.strip():
        return Path(path)

    raise ValueError("Unsupported upload object.")


def upload_files(files: List[gr.File], session: dict | None):
    session = session or _default_session()
    current_history = _welcome_message(session.get("has_docs", False))
    if not files:
        return (
            "No files selected. Please choose PDF or DOCX documents.",
            session,
            _files_table(session.get("files", [])),
            current_history,
            current_history,
        )

    if not isinstance(files, list):
        files = [files]

    prepared = []
    opened_files = []
    for f in files:
        try:
            file_path = _resolve_uploaded_path(f)
        except ValueError:
            continue

        if not file_path.exists():
            return (
                f"Upload failed. File does not exist: {file_path}",
                session,
                _files_table(session.get("files", [])),
                current_history,
                current_history,
            )

        suffix = file_path.suffix.lower()
        mime_type = (
            "application/pdf"
            if suffix == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        file_obj = file_path.open("rb")
        prepared.append(("files", (file_path.name, file_obj, mime_type)))
        opened_files.append(file_obj)

    if not prepared:
        return (
            "No valid files selected. Please upload PDF or DOCX documents.",
            session,
            _files_table(session.get("files", [])),
            current_history,
            current_history,
        )

    try:
        with httpx.Client(timeout=900.0) as client:
            response = client.post(f"{API_BASE_URL}/upload", files=prepared)
            response.raise_for_status()
            data = response.json()
            uploaded_files = data.get("files", [])

            new_session = {"has_docs": True, "files": uploaded_files}

            file_names = ", ".join(uploaded_files) if len(uploaded_files) <= 2 else f"{len(uploaded_files)} files indexed"
            return (
                f"Successfully indexed: {file_names}",
                new_session,
                _files_table(uploaded_files),
                _welcome_message(True),
                _welcome_message(True),
            )
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        suffix = f" {detail}" if detail else " Please check file format."
        error_msg = f"Upload failed.{suffix}"
        return (
            error_msg,
            session,
            _files_table(session.get("files", [])),
            current_history,
            current_history,
        )
    except Exception:
        error_msg = "Upload failed. Please check your connection and try again."
        return (
            error_msg,
            session,
            _files_table(session.get("files", [])),
            current_history,
            current_history,
        )
    finally:
        for file_obj in opened_files:
            file_obj.close()


def ask_question(message: str, history: List[dict[str, Any]], session: dict | None):
    try:
        has_docs = (session or {}).get("has_docs", False)
        history = _normalize_history(history, has_docs)
        message = (message or "").strip()
        if not message:
            return history, history, ""

        if not has_docs:
            history.append({"role": "user", "content": message})
            history.append(
                {
                    "role": "assistant",
                    "content": "Please upload a contract file first. Use Upload & Index to continue.",
                }
            )
            return history, history, ""

        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{API_BASE_URL}/ask", json={"question": message})
            response.raise_for_status()
            data = response.json()

            answer = data.get("answer", "")
            citations = _format_citations(data.get("citations", []))
            full_answer = answer if not citations else f"{answer}\n\n{citations}"

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": full_answer})
            return history, history, ""
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_detail(exc.response)
        assistant_reply = f"Unable to process. {detail}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history, ""
    except Exception as exc:
        error_msg = f"Error: {str(exc)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, history, ""


def summarize_contract(history: List[dict[str, Any]], session: dict | None):
    has_docs = (session or {}).get("has_docs", False)
    history = _normalize_history(history, has_docs)
    prompt = "Provide a comprehensive summary of the contract"
    if not has_docs:
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": "Upload a contract first to proceed."})
        return history, history
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{API_BASE_URL}/summary")
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_detail(exc.response)
        assistant_reply = f"Unable to generate summary. {detail}"
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history
    except Exception:
        assistant_reply = "Service unavailable. Please try again."
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": assistant_reply})
        return history, history

    answer = data.get("answer", "")
    citations = _format_citations(data.get("citations", []))
    full_answer = answer if not citations else f"{answer}\n\n{citations}"
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": full_answer})
    return history, history


def clear_conversation(session: dict | None):
    has_docs = (session or {}).get("has_docs", False)
    fresh = _welcome_message(has_docs)
    return fresh, fresh


def use_quick_prompt(prompt: str, history: List[dict[str, Any]], session: dict | None):
    return ask_question(prompt, history, session)


def quick_payment_terms(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("What are the payment terms and due dates?", history, session)


def quick_termination(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("Explain the termination clause.", history, session)


def quick_risks(history: List[dict[str, Any]], session: dict | None):
    return use_quick_prompt("What are the risky clauses?", history, session)


with gr.Blocks(title="Smart Contract Assistant") as demo:
    with gr.Column(elem_classes=["app-shell"]):
        gr.Markdown(
            "<div class='hero'><h1>Smart Contract Assistant</h1><p>Upload contracts, then ask grounded questions with citations.</p></div>"
        )

        with gr.Row():
            api_status = gr.Textbox(
                label="Backend Status",
                value=check_api_health(),
                interactive=False,
                lines=1,
                scale=5,
            )
            refresh_status = gr.Button("Check API", variant="secondary", scale=1)

        with gr.Row(equal_height=True, scale=1):
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    value=_welcome_message(False),
                    height=520,
                    layout="bubble",
                    buttons=["copy", "copy_all"],
                    elem_classes=["card"],
                )
                with gr.Row(scale=1, elem_classes=["composer-shell"]):
                    user_message = gr.Textbox(
                        show_label=False,
                        container=False,
                        placeholder="Ask a question about the uploaded contract...",
                        lines=1,
                        max_lines=4,
                        submit_btn="Send",
                        elem_id="chat-composer",
                    )

            with gr.Column(scale=1):
                with gr.Column(elem_classes=["card"]):
                    gr.Markdown("### Upload Documents")
                    uploader = gr.File(
                        label="Files (.pdf, .docx)",
                        file_count="multiple",
                        file_types=[".pdf", ".docx"],
                    )
                    upload_button = gr.Button("Upload & Index", variant="primary", scale=1)
                    upload_status = gr.Textbox(
                        label="Upload Status",
                        interactive=False,
                        lines=2,
                        max_lines=2,
                    )
                    indexed_files = gr.Dataframe(
                        headers=["Indexed Files"],
                        datatype=["str"],
                        value=[],
                        interactive=False,
                        row_count=4,
                        column_count=1,
                    )

                with gr.Column(elem_classes=["card"]):
                    gr.Markdown("### Quick Actions")
                    summary_button = gr.Button("Summarize Contract", variant="secondary")
                    with gr.Row(elem_classes=["quick-actions"]):
                        payment_button = gr.Button("Payment Terms")
                        termination_button = gr.Button("Termination")
                        risks_button = gr.Button("Risky Clauses")
                    clear_button = gr.Button("Clear Chat", variant="secondary")

        memory_state = gr.State(_welcome_message(False))
        session_state = gr.State(_default_session())

    demo.load(check_api_health, inputs=[], outputs=[api_status])
    refresh_status.click(check_api_health, inputs=[], outputs=[api_status])

    upload_button.click(
        upload_files,
        inputs=[uploader, session_state],
        outputs=[upload_status, session_state, indexed_files, chatbot, memory_state],
    ).then(check_api_health, inputs=[], outputs=[api_status])

    user_message.submit(
        ask_question,
        inputs=[user_message, memory_state, session_state],
        outputs=[chatbot, memory_state, user_message],
    )

    summary_button.click(
        summarize_contract,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state],
    )

    payment_button.click(
        quick_payment_terms,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message],
    )
    termination_button.click(
        quick_termination,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message],
    )
    risks_button.click(
        quick_risks,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message],
    )
    clear_button.click(
        clear_conversation,
        inputs=[session_state],
        outputs=[chatbot, memory_state],
    )


if __name__ == "__main__":
    launch_kwargs = {
        "server_name": "127.0.0.1",
        "css": CUSTOM_CSS,
    }
    configured_port = os.getenv("GRADIO_SERVER_PORT")
    if configured_port:
        launch_kwargs["server_port"] = int(configured_port)
    demo.launch(**launch_kwargs)
