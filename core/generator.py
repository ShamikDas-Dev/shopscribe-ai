from __future__ import annotations

import os
from typing import Any

from core.language_checks import has_bengali_prose
from core.prompts import build_messages
from core.schemas import ContentPack, ProductFacts

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_LOCAL_MODEL = "qwen3:4b"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


def _client(host: str = DEFAULT_HOST):
    try:
        import ollama
    except ImportError as exc:
        raise RuntimeError(
            "The Ollama Python client is not installed. Run `pip install ollama` to use local inference."
        ) from exc
    return ollama.Client(host=host, timeout=180.0)


def list_local_models(host: str = DEFAULT_HOST) -> list[str]:
    """Return model names already available in the configured Ollama instance."""
    try:
        response = _client(host).list()
    except Exception as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {host}. Start Ollama and check the host setting. Details: {exc}"
        ) from exc

    model_items: Any = getattr(response, "models", None)
    if model_items is None and isinstance(response, dict):
        model_items = response.get("models", [])
    names: list[str] = []
    for item in model_items or []:
        name = getattr(item, "model", None) or getattr(item, "name", None)
        if name is None and isinstance(item, dict):
            name = item.get("model") or item.get("name")
        if name:
            names.append(str(name))
    return sorted(set(names))


def _parse_content(content: Any) -> ContentPack:
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The model returned an empty response. Try again or select a different model.")
    try:
        return ContentPack.model_validate_json(content)
    except Exception as exc:
        raise RuntimeError(
            f"The model response did not match the required content schema: {exc}"
        ) from exc


def _ollama_chat_for_content(
    client,
    model: str,
    messages: list[dict[str, str]],
) -> ContentPack:
    try:
        response = client.chat(
            model=model,
            messages=messages,
            format=ContentPack.model_json_schema(),
            options={"temperature": 0.25},
        )
    except Exception as exc:
        detail = str(exc)
        if "not found" in detail.lower() or "pull" in detail.lower():
            detail += f". Download the selected model with: ollama pull {model}"
        raise RuntimeError(f"Ollama generation request failed: {detail}") from exc

    message = getattr(response, "message", None)
    content = getattr(message, "content", None) if message is not None else None
    if content is None and isinstance(response, dict):
        content = response.get("message", {}).get("content")
    return _parse_content(content)


def _groq_chat_for_content(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
) -> ContentPack:
    """Generate using Groq-hosted open-weight models. The API key is never logged."""
    if not api_key.strip():
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it in Streamlit Community Cloud → "
            "App settings → Secrets, or set the GROQ_API_KEY environment variable locally."
        )

    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            "The Groq SDK is not installed. Run `pip install groq` or redeploy after updating requirements.txt."
        ) from exc

    try:
        client = Groq(api_key=api_key.strip(), timeout=120.0, max_retries=1)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        detail = str(exc)
        lower = detail.lower()
        if "401" in lower or "authentication" in lower or "invalid api key" in lower:
            detail = "Groq rejected the API key. Check that GROQ_API_KEY is set correctly in app secrets."
        elif "429" in lower or "rate limit" in lower or "quota" in lower:
            detail = "Groq rate limit or usage quota reached. Wait for the limit to reset or check your Groq console."
        raise RuntimeError(f"Groq generation request failed: {detail}") from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq returned an unexpected response. Please retry.") from exc
    return _parse_content(content)


def _ensure_language(
    generate_once,
    facts: ProductFacts,
    language: str,
    tone: str,
) -> ContentPack:
    pack = generate_once(build_messages(facts, language, tone))
    if language == "Bengali" and not has_bengali_prose(
        pack.product_description,
        pack.instagram_caption,
        pack.whatsapp_message,
    ):
        pack = generate_once(build_messages(facts, language, tone, strict_bengali_retry=True))
        if not has_bengali_prose(
            pack.product_description,
            pack.instagram_caption,
            pack.whatsapp_message,
        ):
            raise RuntimeError(
                "The selected model did not generate Bengali-script text after a retry. "
                "Try another multilingual model and verify the wording with a fluent Bengali speaker."
            )
    return pack


def generate_content(
    facts: ProductFacts,
    language: str = "English",
    tone: str = "Friendly",
    model: str = DEFAULT_LOCAL_MODEL,
    host: str = DEFAULT_HOST,
    provider: str = "Ollama",
    api_key: str | None = None,
) -> ContentPack:
    """Generate and validate a content pack with Ollama locally or Groq-hosted open-weight inference.

    With provider='Ollama', inference is local by default.
    With provider='Groq', prompts and product information are sent to Groq's hosted API.
    Bengali generation gets one corrective retry when the first result fails a script check.
    """
    chosen_model = model.strip()
    if not chosen_model:
        raise ValueError("Enter a model name.")

    if provider == "Ollama":
        client = _client(host)
        return _ensure_language(
            lambda messages: _ollama_chat_for_content(client, chosen_model, messages),
            facts,
            language,
            tone,
        )
    if provider == "Groq":
        chosen_key = api_key or os.getenv("GROQ_API_KEY", "")
        return _ensure_language(
            lambda messages: _groq_chat_for_content(chosen_key, chosen_model, messages),
            facts,
            language,
            tone,
        )
    raise ValueError("Unsupported provider. Choose Ollama or Groq.")
