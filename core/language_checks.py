from __future__ import annotations

import re

BENGALI_CHAR_PATTERN = re.compile(r"[\u0980-\u09FF]")
LETTER_PATTERN = re.compile(r"[A-Za-z\u0980-\u09FF]")


def has_bengali_prose(*texts: str, minimum_bengali_chars: int = 12, minimum_ratio: float = 0.15) -> bool:
    """Heuristically check that generated prose contains Bengali-script text.

    This is a script check, not a full language-quality detector. It intentionally checks
    prose fields rather than hashtags, because hashtags alone should not satisfy the language
    requirement.
    """
    combined = "\n".join(text or "" for text in texts)
    bengali_count = len(BENGALI_CHAR_PATTERN.findall(combined))
    letters = LETTER_PATTERN.findall(combined)
    if not letters:
        return False
    return bengali_count >= minimum_bengali_chars and (bengali_count / len(letters)) >= minimum_ratio
