import pytest

from core.generator import _parse_content
from core.schemas import ContentPack


def valid_json() -> str:
    return """
    {
      "product_title": "Hydrating Moisturizer",
      "product_description": "A lightweight moisturizer in a 50 g pack.",
      "instagram_caption": "Discover the product at our store.",
      "whatsapp_message": "Contact us for availability.",
      "hashtags": ["#Skincare", "#ShopLocal"],
      "review_notes": []
    }
    """


def test_parse_content_accepts_valid_json_schema():
    result = _parse_content(valid_json())
    assert isinstance(result, ContentPack)
    assert result.product_title == "Hydrating Moisturizer"


def test_parse_content_rejects_malformed_or_incomplete_json():
    with pytest.raises(RuntimeError, match="did not match"):
        _parse_content('{"product_title": "Incomplete"}')


def test_parse_content_rejects_empty_response():
    with pytest.raises(RuntimeError, match="empty response"):
        _parse_content("  ")
