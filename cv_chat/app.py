import os
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import dotenv
from flask import Flask, request, send_from_directory
from openai import AzureOpenAI

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR.parent / "docs"

app = Flask(__name__, static_folder=str(DOCS_DIR), static_url_path="")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()



context_path = BASE_DIR / "andrei_context.txt"


class _CVTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip = True
        if tag in {"h1", "h2", "h3", "p", "li"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = False
        if tag in {"h1", "h2", "h3", "p", "li"}:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self):
        raw = " ".join(self._chunks)
        normalized = re.sub(r"[ \t]+", " ", raw)
        normalized = re.sub(r"\n{2,}", "\n", normalized)
        return normalized.strip()


def build_context_from_cv(cv_path: Path, extra_context: str) -> str:
    if not cv_path.exists():
        return extra_context
    parser = _CVTextParser()
    parser.feed(cv_path.read_text(encoding="utf-8"))
    cv_text = unescape(parser.text())
    cv_text = re.sub(r"[ \t]+\n", "\n", cv_text)

    git_block = ""
    if "Git Repos:" in extra_context:
        parts = extra_context.split("Git Repos:", 1)
        git_block = "Git Repos:\n" + parts[1].strip()

    if git_block:
        return f"{cv_text}\n\n{git_block}"
    return cv_text


if context_path.exists():
    raw_context = context_path.read_text(encoding="utf-8").strip()
else:
    raw_context = ""

andrei_context = build_context_from_cv(DOCS_DIR / "index.html", raw_context)

conversation = [
    {
        "role": "system",
        "content": (
            "You are a concise assistant that only answers questions about Andrei Sirazitdinov's skills, competencies, prrojects, and background. "
            "Reply in short bullet points (no bold). If the question is not about Andrei's skills, competencies, projects, and background, say you can only answer "
            "questions about his skills, competencies, projects, and background and ask the user to rephrase. If a user pastes an open position description, read it and say whether Andrei is a good fit for it."
            + (f"\n\nContext about Andrei:\n{andrei_context}" if andrei_context else "")
        ),
    }
]

@app.route("/")
def index():
    return send_from_directory(DOCS_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(DOCS_DIR, filename)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    conversation.append({"role": "user", "content": user_input})

    if not DEPLOYMENT_NAME:
        return "Chat is not configured. Missing AZURE_OPENAI_DEPLOYMENT.", 500

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=conversation
    )

    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})

    return reply

if __name__ == '__main__':
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
