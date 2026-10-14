from core.schemas import ContentPack, ProductFacts
from core.validators import validate_content_pack


def make_pack(description: str, instagram: str = "A useful product.") -> ContentPack:
    return ContentPack(
        product_title="Sample product",
        product_description=description,
        instagram_caption=instagram,
        whatsapp_message="Visit our store for details.",
        hashtags=["#ShopLocal"],
    )


def test_flags_unsupported_medical_claim():
    facts = ProductFacts(product_name="Face cream", verified_features=["50 g pack"])
    pack = make_pack("This cream cures acne.")
    notes = validate_content_pack(pack, facts)
    assert any("medical or therapeutic claim" in note for note in notes)


def test_flags_price_not_in_product_facts():
    facts = ProductFacts(product_name="Face cream", verified_features=["50 g pack"], selling_price=299)
    pack = make_pack("Available today for ₹199.")
    notes = validate_content_pack(pack, facts)
    assert any("does not match" in note for note in notes)


def test_does_not_flag_supported_price():
    facts = ProductFacts(product_name="Face cream", verified_features=["50 g pack"], selling_price=299)
    pack = make_pack("Available for ₹299.")
    notes = validate_content_pack(pack, facts)
    assert not any("price" in note.lower() for note in notes)
