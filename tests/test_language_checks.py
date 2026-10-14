from core.language_checks import has_bengali_prose
from core.prompts import build_messages
from core.schemas import ProductFacts


def test_bengali_script_passes_language_check():
    assert has_bengali_prose(
        "এই পণ্যটি আপনার দৈনন্দিন রুটিনে ব্যবহার করতে পারেন।",
        "নতুন পণ্যটি সম্পর্কে জানতে আমাদের সঙ্গে যোগাযোগ করুন।",
        "দোকানে এসে দেখে নিন।",
    )


def test_english_only_prose_fails_bengali_language_check():
    assert not has_bengali_prose(
        "Try this product in your daily routine.",
        "Contact us to learn more about this product.",
        "Visit our store today.",
    )


def test_bengali_has_explicit_script_instructions():
    facts = ProductFacts(product_name="Moisturizer", verified_features=["50 g pack"])
    messages = build_messages(facts, "Bengali", "Friendly")
    combined = "\n".join(message["content"] for message in messages)
    assert "Bengali Unicode script" in combined
    assert "no transliteration" in combined


def test_strict_bengali_retry_adds_correction_message():
    facts = ProductFacts(product_name="Moisturizer", verified_features=["50 g pack"])
    messages = build_messages(facts, "Bengali", "Friendly", strict_bengali_retry=True)
    assert len(messages) == 3
    assert "LANGUAGE CORRECTION REQUIRED" in messages[-1]["content"]
