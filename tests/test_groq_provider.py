import sys
from types import SimpleNamespace

import pytest

from core.generator import _groq_chat_for_content


VALID_RESPONSE = """
{
  "product_title": "Hydrating Moisturizer",
  "product_description": "A lightweight moisturizer in a 50 g pack.",
  "instagram_caption": "Discover it at our store.",
  "whatsapp_message": "Contact us for availability.",
  "hashtags": ["#Skincare"],
  "review_notes": []
}
"""


def test_groq_provider_parses_json_response(monkeypatch):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=VALID_RESPONSE))]
            )

    class FakeGroq:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=FakeGroq))
    pack = _groq_chat_for_content(
        "test-key-not-real",
        "openai/gpt-oss-20b",
        [{"role": "user", "content": "Return a JSON content pack."}],
    )

    assert pack.product_title == "Hydrating Moisturizer"
    assert captured["model"] == "openai/gpt-oss-20b"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["client_kwargs"]["api_key"] == "test-key-not-real"


def test_groq_provider_rejects_missing_key():
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        _groq_chat_for_content(
            "",
            "openai/gpt-oss-20b",
            [{"role": "user", "content": "test"}],
        )
