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

body, .gradio-container {
  font-family: "Manrope", sans-serif !important;
  color: var(--text-main) !important;
  background:
    radial-gradient(circle at top right, #e0f2fe 0%, transparent 42%),
    radial-gradient(circle at 10% 20%, #dbeafe 0%, transparent 34%),
    var(--bg-soft) !important;
}

.app-shell {
  max-width: 1120px;
  margin: 0 auto;
}

.panel {
  border: 1px solid var(--line) !important;
  border-radius: 18px !important;
  background: var(--panel-bg) !important;
  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.05) !important;
}

.hero {
  padding: 8px 2px 12px 2px;
}

.hero h1 {
  margin: 0;
  font-size: 2.05rem;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.hero p {
  margin: 8px 0 0 0;
  color: var(--text-subtle);
  font-size: 1rem;
}

.pill {
  display: inline-block;
  margin-top: 12px;
  background: #e0f2fe;
  color: #075985;
  border: 1px solid #bae6fd;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.82rem;
  font-weight: 700;
}

.gr-chatbot {
  min-height: 490px !important;
}

.gr-button-primary {
  background: linear-gradient(90deg, var(--accent), var(--accent-strong)) !important;
  border: none !important;
}

.status-box textarea {
  font-size: 0.9rem !important;
}

.composer-shell {
  margin-top: 10px;
  padding: 10px 12px !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 22px !important;
  background: #ffffff !important;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06) !important;
}

#chat-composer {
  margin-bottom: 0 !important;
}

#chat-composer textarea {
  border: none !important;
  box-shadow: none !important;
  padding: 10px 6px !important;
  font-size: 1rem !important;
  line-height: 1.5 !important;
}

#chat-composer textarea:focus {
  border: none !important;
  box-shadow: none !important;
}

.composer-hint {
  margin-top: 6px !important;
  color: var(--text-subtle) !important;
  font-size: 0.82rem !important;
}

.workflow-box {
  margin: 6px 0 14px 0 !important;
  padding: 10px 14px !important;
  border: 1px solid #dbeafe !important;
  background: #f0f9ff !important;
  color: #0c4a6e !important;
  border-radius: 12px !important;
  font-size: 0.92rem !important;
}

.quick-actions {
  margin-top: 2px !important;
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
            "Your documents are ready. Ask a question or use one of the quick actions below.\n\n"
            "Tip: Ask specific questions like 'What are late payment penalties?' for better answers."
        )
    else:
        text = (
            "Welcome. Start by uploading one or more contract files on the right panel.\n\n"
            "After upload, you can ask questions, request a summary, or check specific risk clauses."
        )
    return [{"role": "assistant", "content": text}]


def _files_table(file_names: List[str]) -> List[List[str]]:
    return [[name] for name in file_names]


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
            _files_table(session.get("files", [])),
            "Step 1 of 2: Upload a contract file to begin.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "No files uploaded yet.",
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
            return (
                f"{data.get('message')}\nFiles: {', '.join(uploaded_files)}",
                session,
                _files_table(uploaded_files),
                "Step 2 of 2: Ask a question in chat. You can also click 'Summarize Contract'.",
                _welcome_message(True),
                _welcome_message(True),
                "Documents indexed successfully. You are ready to chat.",
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
            _files_table(session.get("files", [])),
            "Upload failed. Please verify file type/contents and try again.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "Upload failed. The assistant is not ready yet.",
        )
    except Exception as exc:
        return (
            f"Upload failed: {exc}",
            session,
            _files_table(session.get("files", [])),
            "Upload failed due to a local/network issue. Retry after checking API health.",
            _welcome_message(session.get("has_docs", False)),
            _welcome_message(session.get("has_docs", False)),
            "Upload failed. The assistant is not ready yet.",
        )
    finally:
        for _, (_, file_obj, _) in prepared:
            file_obj.close()


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


with gr.Blocks(
    title="Smart Contract Assistant",
) as demo:
    with gr.Column(elem_classes=["app-shell"]):
        gr.Markdown(
            """
<div class="hero">
  <h1>Smart Contract Assistant</h1>
  <p>Upload agreements, ask direct questions, and get citation-backed answers.</p>
  <span class="pill">Simple, fast, and built for clarity</span>
</div>
""",
        )

        memory_state = gr.State(_welcome_message(False))
        session_state = gr.State({"has_docs": False, "files": []})
        workflow_state = gr.Markdown(
            "Step 1 of 2: Upload a contract file to begin.",
            elem_classes=["workflow-box"],
        )

        with gr.Row(equal_height=True):
            with gr.Column(scale=7, elem_classes=["panel"]):
                chatbot = gr.Chatbot(
                    label="Contract Chat",
                    value=_welcome_message(False),
                    height=520,
                    layout="bubble",
                    buttons=["copy", "copy_all"],
                    placeholder="Ask a question about your uploaded contract files to begin.",
                )
                with gr.Row(elem_classes=["composer-shell"]):
                    user_message = gr.Textbox(
                        show_label=False,
                        container=False,
                        placeholder="Message Smart Contract Assistant...",
                        lines=1,
                        max_lines=8,
                        autofocus=True,
                        submit_btn="Send",
                        elem_id="chat-composer",
                    )
                gr.Markdown(
                    '<div class="composer-hint">Press Enter to send. Use Shift+Enter for a new line.</div>'
                )
                with gr.Row(elem_classes=["quick-actions"]):
                    quick_btn_1 = gr.Button("Payment Terms")
                    quick_btn_2 = gr.Button("Termination Clause")
                    quick_btn_3 = gr.Button("Risky Clauses")
                with gr.Row():
                    summary_button = gr.Button("Summarize Contract")
                    clear_button = gr.Button("Clear Chat")

            with gr.Column(scale=5, elem_classes=["panel"]):
                gr.Markdown("### Upload Documents")
                uploader = gr.File(
                    label="PDF or DOCX files",
                    file_count="multiple",
                    file_types=[".pdf", ".docx"],
                )
                upload_button = gr.Button("Upload and Index", variant="primary")
                upload_status = gr.Textbox(
                    label="Upload Status",
                    placeholder="No documents uploaded yet.",
                    interactive=False,
                    lines=4,
                    elem_classes=["status-box"],
                )
                indexed_files = gr.Dataframe(
                    headers=["Indexed files"],
                    datatype=["str"],
                    value=[],
                    interactive=False,
                    wrap=True,
                    row_count=(3, "dynamic"),
                    column_count=(1, "fixed"),
                    label="Current Contract Set",
                )
                health_button = gr.Button("Check API Health")
                health_status = gr.Textbox(
                    label="API Health",
                    interactive=False,
                    lines=3,
                    elem_classes=["status-box"],
                )
                assistant_status = gr.Textbox(
                    label="Assistant Status",
                    value="No files uploaded yet.",
                    interactive=False,
                    lines=2,
                    elem_classes=["status-box"],
                )
                gr.Examples(
                    examples=[
                        ["What are the obligations of each party?"],
                        ["List key dates and deadlines in this agreement."],
                        ["Are there clauses that increase legal risk?"],
                    ],
                    inputs=user_message,
                    label="Quick Prompts",
                )

    upload_button.click(
        upload_files,
        inputs=[uploader, session_state],
        outputs=[upload_status, session_state, indexed_files, workflow_state, chatbot, memory_state, assistant_status],
    )
    health_button.click(check_api_health, outputs=[health_status])
    user_message.submit(
        ask_question,
        inputs=[user_message, memory_state, session_state],
        outputs=[chatbot, memory_state, user_message, assistant_status],
    )
    summary_button.click(
        summarize_contract,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, assistant_status],
    )
    clear_button.click(
        clear_conversation,
        inputs=[session_state],
        outputs=[chatbot, memory_state, assistant_status],
    )
    quick_btn_1.click(
        quick_payment_terms,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message, assistant_status],
    )
    quick_btn_2.click(
        quick_termination,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message, assistant_status],
    )
    quick_btn_3.click(
        quick_risks,
        inputs=[memory_state, session_state],
        outputs=[chatbot, memory_state, user_message, assistant_status],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=gr.themes.Soft(primary_hue="sky", secondary_hue="cyan", neutral_hue="slate"),
        css=CUSTOM_CSS,
    )

