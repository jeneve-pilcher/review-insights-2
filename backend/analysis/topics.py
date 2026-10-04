import re
from collections import Counter

import nltk
from nltk.corpus import stopwords

nltk.download("stopwords", quiet=True)

_STOP_WORDS = set(stopwords.words("english"))
# Generic review filler words that pass the stopword filter but rarely
# signal a specific topic - filtered out so keywords are more informative.
_EXTRA_STOP_WORDS = {
    "place", "food", "get", "got", "one", "also", "really", "would", "us",
    "went", "go", "back", "time", "great", "good", "nice", "im", "ive",
}


def top_keywords(texts: list[str], top_n: int = 8) -> list[dict]:
    """
    Simple, fast frequency-based keyword extraction - not full topic
    modeling (no LDA/embeddings). Good enough to surface "what people keep
    mentioning" without the latency or complexity of a heavier NLP pipeline.
    """
    counts = Counter()
    for text in texts:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        for w in words:
            if w not in _STOP_WORDS and w not in _EXTRA_STOP_WORDS:
                counts[w] += 1

    return [{"word": word, "count": count} for word, count in counts.most_common(top_n)]
