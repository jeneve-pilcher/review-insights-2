import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon", quiet=True)

_SIA = SentimentIntensityAnalyzer()

# Phrases that suggest a customer is comparing current experience to a past
# one unfavorably - a leading indicator of drift before scores visibly move.
DRIFT_PHRASES = [
    "used to be", "not like it used to", "went downhill", "changed the recipe",
    "formula change", "not the same anymore", "quality dropped", "isn't what it was",
]

WAIT_TIME_PHRASES = [
    "wait time", "waited", "long wait", "slow service", "took forever",
    "understaffed", "short staffed", "long line",
]


def score_sentiment(text: str) -> float:
    return _SIA.polarity_scores(text)["compound"]


def contains_any_phrase(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)
