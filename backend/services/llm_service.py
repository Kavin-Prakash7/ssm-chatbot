
import os
from pathlib import Path

import google.generativeai as genai
import requests
from dotenv import load_dotenv

from backend.services.response_service import build_button, create_response


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
REQUEST_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))


def _system_prompt(language):
    response_language = "Bahasa Melayu" if language == "ms" else "English"
    return f"""
You are SSM eInfo Assistant, a premium guided assistant for SSM eInfo only.

Your scope is strictly limited to:
- greetings
- onboarding
- conversational support
- help requests
- platform explanations
- assistant-style guidance about SSM eInfo, company documents, and business document preparation

You must never take over or imitate:
- FAQ button responses
- cart logic
- checkout logic
- deterministic routing
- company search logic
- document flow state handling

Behavior rules:
- Stay focused on SSM eInfo and related document/business guidance only.
- Do not provide unrelated internet knowledge or drift into random topics.
- If asked something outside scope, politely redirect the user to supported SSM eInfo guidance.
- Keep replies concise, premium, and guided.
- Use short paragraphs or short bullet-style lines without markdown tables.
- If the user needs a deterministic action, guide them to use the available menu options.
- Respond entirely in {response_language}.
""".strip()


def _fallback_message(language):
    if language == "ms":
        return (
            "Saya sedia membantu dengan panduan SSM eInfo, penerangan platform, dan bantuan permulaan. "
            "Untuk tindakan seperti carian syarikat, dokumen, atau pembayaran, sila gunakan menu yang tersedia."
        )
    return (
        "I can help with SSM eInfo guidance, platform explanations, and onboarding support. "
        "For actions like company search, documents, or checkout, please use the available menu options."
    )


def _sanitize_reply(text, language):
    cleaned = " ".join((text or "").split())
    return cleaned or _fallback_message(language)


def _gemini_response(message, language):
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key is not configured.")

    genai.configure(api_key=GEMINI_API_KEY)
    prompt = f"{_system_prompt(language)}\n\nUser message: {message}\nAssistant reply:"
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.4,
            "max_output_tokens": 280,
            "top_p": 0.9,
        },
    )
    text = getattr(response, "text", "")
    return _sanitize_reply(text, language)


def _openai_response(message, language):
    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key is not configured.")

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.4,
        "max_tokens": 280,
        "messages": [
            {"role": "system", "content": _system_prompt(language)},
            {"role": "user", "content": message},
        ],
    }
    response = requests.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return _sanitize_reply(text, language)


def get_conversational_reply(message, language):
    errors = []

    try:
        return _gemini_response(message, language)
    except Exception as exc:
        errors.append(f"gemini: {exc}")

    try:
        return _openai_response(message, language)
    except Exception as exc:
        errors.append(f"openai: {exc}")

    return _fallback_message(language)


def handle_llm_message(message, language):
    reply = get_conversational_reply(message, language)
    return create_response(
        response_type="llm",
        title="Assistant" if language == "en" else "Pembantu",
        message=reply,
        buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
        data={"provider_order": ["gemini", "openai"]},
    )
