from functools import lru_cache

MODEL_NAME = 'ProsusAI/finbert'


@lru_cache(maxsize=1)
def _get_classifier():
    # Loaded lazily: the ~440 MB model download and torch import must not block API boot.
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    return pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)


def score_headlines(headlines: list[str]) -> list[float]:
    if not headlines:
        return [0.0]
    out = _get_classifier()(headlines, truncation=True)
    scores = []
    for item in out:
        label = item['label'].lower()
        val = item['score']
        scores.append(val if 'positive' in label else -val if 'negative' in label else 0.0)
    return scores
