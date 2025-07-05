from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax

class FinBertSentimentAnalyzer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
        self.model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

    def analyze_sentiment(self, text: str) -> dict:
        if len(text) > 1000:  # Tighter limit for stability
            text = text[:1000]

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )

        outputs = self.model(**inputs)
        probs = softmax(outputs.logits, dim=1)[0]

        sentiment_scores = {
            "positive": float(probs[0]),
            "negative": float(probs[1]),
            "neutral": float(probs[2])
        }

        sentiment_label = max(sentiment_scores, key=sentiment_scores.get)

        return {
            "label": sentiment_label,
            "scores": sentiment_scores
        }
