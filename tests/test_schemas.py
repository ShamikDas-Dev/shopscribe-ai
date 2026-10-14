import pytest
from pydantic import ValidationError

from core.schemas import ContentPack, ProductFacts


def test_product_facts_requires_at_least_one_feature():
    with pytest.raises(ValidationError):
        ProductFacts(product_name="Moisturizer", verified_features=[])


def test_product_facts_strips_blank_features():
    facts = ProductFacts(product_name=" Moisturizer ", verified_features=["  Lightweight  ", "   "])
    assert facts.product_name == "Moisturizer"
    assert facts.verified_features == ["Lightweight"]


def test_content_pack_accepts_expected_fields():
    pack = ContentPack(
        product_title="Hydrating Moisturizer",
        product_description="A lightweight moisturizer.",
        instagram_caption="Discover this moisturizer.",
        whatsapp_message="Available in store.",
        hashtags=["#Skincare"],
    )
    assert pack.hashtags == ["#Skincare"]
    assert pack.review_notes == []
