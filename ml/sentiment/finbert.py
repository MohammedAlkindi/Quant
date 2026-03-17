from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

MODEL_NAME = 'ProsusAI/finbert'
_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
_model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
_classifier = pipeline('sentiment-analysis', model=_model, tokenizer=_tokenizer)


def score_headlines(headlines: list[str]) -> list[float]:
    if not headlines:
        return [0.0]
    out = _classifier(headlines, truncation=True)
    scores = []
    for item in out:
        label = item['label'].lower()
        val = item['score']
        scores.append(val if 'positive' in label else -val if 'negative' in label else 0.0)
    return scores
