from transformers import pipeline

THEME_LABELS = ["Product Quality", "Pricing", "Weekend Communication", "Staff Behavior"]

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33",
        )
    return _classifier


def classify_themes(texts: list[str], threshold: float = 0.4, batch_size: int = 16) -> list[list[str]]:
    """Returns, per text, the list of THEME_LABELS whose confidence >= threshold."""
    if not texts:
        return []

    classifier = get_classifier()
    results = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        outputs = classifier(batch, THEME_LABELS, multi_label=True)
        if isinstance(outputs, dict):
            outputs = [outputs]
        for out in outputs:
            matched = [lab for lab, score in zip(out["labels"], out["scores"]) if score >= threshold]
            results.append(matched)
    return results
