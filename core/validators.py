from __future__ import annotations

import re

from core.schemas import ContentPack, ProductFacts

# Flag these for human review unless the source facts explicitly support the claim.
CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("medical or therapeutic claim", re.compile(r"\b(cures?|treats?|heals?|prevents? disease|anti[- ]?acne treatment)\b", re.I)),
    ("clinical evidence claim", re.compile(r"\b(clinically proven|clinically tested|dermatologist[- ]approved|dermatologist tested)\b", re.I)),
    ("guarantee or absolute claim", re.compile(r"\b(100\s*%\s*safe|guaranteed results?|permanent results?|zero side effects?)\b", re.I)),
    ("skin-lightening claim", re.compile(r"\b(skin whitening|whitens? skin|fairness guaranteed)\b", re.I)),
)

PRICE_PATTERN = re.compile(r"(?:₹|\bRs\.?\s*|\bINR\s*)([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I)


def validate_content_pack(pack: ContentPack, facts: ProductFacts) -> list[str]:
    """Return review notes for detectable risks; this is not a truth verification system."""
    notes: list[str] = []
    generated = "\n".join(
        [pack.product_title, pack.product_description, pack.instagram_caption, pack.whatsapp_message, *pack.hashtags]
    )
    source = " ".join(
        [facts.product_name, facts.brand or "", facts.category, *facts.verified_features]
    ).casefold()

    for label, pattern in CLAIM_PATTERNS:
        for match in pattern.finditer(generated):
            matched_phrase = match.group(0).casefold()
            # A text match in the source is not proof, but avoids some obvious duplicate warnings.
            if matched_phrase not in source:
                notes.append(f"Review the {label}: ‘{match.group(0)}’ is not clearly supported by the supplied facts.")
                break

    known_prices = {
        round(value, 2)
        for value in (facts.selling_price, facts.mrp)
        if value is not None
    }
    for match in PRICE_PATTERN.finditer(generated):
        try:
            mentioned_price = round(float(match.group(1).replace(",", "")), 2)
        except ValueError:
            continue
        if known_prices and mentioned_price not in known_prices:
            notes.append(
                f"Check the price ₹{mentioned_price:,.2f}; it does not match the product prices entered in the form."
            )
            break
        if not known_prices:
            notes.append("The generated content contains a price, but no price was supplied in the form. Verify it before publishing.")
            break

    return list(dict.fromkeys(notes))
