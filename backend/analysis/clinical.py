"""Clinical-language handling for tone scoring.

A review that says "my pain was gone in minutes" is praise, but a general tone scorer reads "pain" as negative. For
healthcare industries, words that describe the CONDITION (not the experience) are replaced with a neutral word in
COPIES of the reviews used for tone analysis. The original review text is never changed, and theme matching and star
ratings are unaffected."""
import re
from typing import List

CLINICAL_TERMS = [
    "pain", "painful", "aches", "ache", "sore", "soreness", "sick", "sickness", "illness", "disease", "infection", "infected",
    "injury", "injured", "fracture", "fractured", "wound", "bleeding", "fever", "cough", "vomiting", "nausea", "cancer",
    "tumor", "surgery", "surgical", "emergency", "accident", "anxiety", "depression", "diagnosis", "symptoms", "swelling",
    "rash", "allergic", "allergy", "toothache", "cavity", "cavities", "decay",
]
_PATTERN = re.compile(r"(?<![a-z])(?:" + "|".join(sorted(map(re.escape, CLINICAL_TERMS), key=len, reverse=True)) + r")(?![a-z])", re.IGNORECASE)
NEUTRAL = "condition"


def neutralize(text: str) -> str:
    return _PATTERN.sub(NEUTRAL, text or "")


def neutral_copies(reviews: List[dict]) -> List[dict]:
    """Copies of the reviews with clinical words neutralized, for tone analysis only."""
    return [{**r, "text": neutralize(r["text"])} if r.get("text") else r for r in reviews]
