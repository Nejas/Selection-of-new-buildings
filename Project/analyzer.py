import re

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class SentimentAnalyzer:
    """
    Анализатор тональности с постобработкой:
    - порог уверенности
    - лексическая коррекция
    """

    LABELS = {
        0: "negative",
        1: "neutral",
        2: "positive"
    }

    NEGATIVE_KEYWORDS = {
        "плохо", "ужас", "кошмар", "отвратительно", "задержка",
        "обман", "проблема", "дефект", "брак", "штраф",
        "монополизация", "банкротство", "долгострой", "нарушение",
        "прокуратура", "генпрокуратура", "роскомнадзор",
        "росреестр", "ответчик"
    }
    NEGATIVE_PATTERNS = (
        r"\bвозбудил[аио]?\s+дел[оа]\b",
        r"\bдел[оа]\s+против\b",
        r"\bфас\b",
        r"\bсуд\b",
        r"\bиск\b",
        r"\bиск\s+к\b",
        r"\bподал[аио]?\s+иск\b",
        r"\bпризнал[аи]?\s+ненадлежащ",
        r"\bпривлек[а-я]*\s+к\s+ответственности\b",
        r"\bнарушени[ея]\s+антимонопольн",
        r"\bсрыв\s+срок",
        r"\bобманут[а-я]*\s+дольщик",
        r"\bпровер(ит|ила|или|яет|ку)\b",
    )
    NEUTRAL_PATTERNS = (
        r"\bувеличил[аио]?\s+дол[юи]\b",
        r"\bснизил[аио]?\s+дол[юи]\b",
        r"\bдол[яюи]\s+в\s+капитал[еа]\b",
        r"\bкапитал[еа]\s+.+\bпик\s+сз\b",
        r"\bобратн[а-я]*\s+сплит[а-я]*\s+акци",
        r"\bструктура\s+групп[ыа]\b",
        r"\bпродал[аио]?\s+.+\b(торговый\s+центр|тц|актив)",
        r"\bизбавля[а-я]+\s+от\s+непрофильн[а-я]+\s+актив",
        r"\bнепрофильн[а-я]+\s+актив",
        r"\bкотировк[аи]\b",
        r"\bакци[ияй]\b",
    )
    POSITIVE_PATTERNS = (
        r"\bпоявит[сш]я\s+жилой\s+комплекс\b",
        r"\bстроительством\s+будет\s+заниматься\b",
        r"\bпостроит\b",
        r"\bпостроят\b",
        r"\bпостроит\s+многофункциональн[а-я]+\s+центр\b",
        r"\bпоучаству[а-я]+\s+в\s+программ[еы]\s+крт\b",
        r"\bначал[аио]?\s+строительств",
        r"\bполучил[аио]?\s+разрешени[ея]\s+на\s+строительств",
        r"\bввел[аио]?\s+в\s+эксплуатаци",
        r"\bсдал[аио]?\s+.+\b(дом|корпус|жилой\s+комплекс|жк)\b",
    )

    POSITIVE_KEYWORDS = {
        "хорошо", "отлично", "прекрасно", "доволен", "рекомендую",
        "качественно", "нравится"
    }

    CONFIDENCE_THRESHOLD = 0.50

    def __init__(self, model_name="blanchefort/rubert-base-cased-sentiment"):
        print(" [Sentiment] Загрузка модели тональности...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

        self.model.eval()
        self.device = torch.device("cpu")
        self.model.to(self.device)
        print("[Sentiment] Модель загружена")

    def _keyword_correction(self, text: str) -> str | None:
        """Лексическая коррекция по ключевым словам."""
        text = text.lower()

        if any(re.search(pattern, text) for pattern in self.NEGATIVE_PATTERNS):
            return "negative"

        if any(word in text for word in self.NEGATIVE_KEYWORDS):
            return "negative"

        if any(re.search(pattern, text) for pattern in self.POSITIVE_PATTERNS):
            return "positive"

        if any(re.search(pattern, text) for pattern in self.NEUTRAL_PATTERNS):
            return "neutral"

        if any(word in text for word in self.POSITIVE_KEYWORDS):
            return "positive"

        return None

    def predict_batch(self, texts, batch_size=16):
        results = []

        if not texts:
            print("[Sentiment] Пустой список текстов")
            return results

        print(f" [Sentiment] Анализ {len(texts)} текстов (batch={batch_size})")

        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                tokens = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=256,
                    return_tensors="pt"
                ).to(self.device)

                outputs = self.model(**tokens)
                probs = torch.softmax(outputs.logits, dim=1)

                for j, text in enumerate(batch):
                    probs_row = probs[j]
                    max_prob = probs_row.max().item()
                    label_id = torch.argmax(probs_row).item()
                    model_label = self.LABELS[label_id]

                    # 1️ Лексическая коррекция
                    keyword_label = self._keyword_correction(text)

                    if keyword_label:
                        final_label = keyword_label
                        reason = "keyword"
                    # 2️ Порог уверенности
                    elif max_prob < self.CONFIDENCE_THRESHOLD:
                        final_label = "neutral"
                        reason = "low_confidence"
                    else:
                        final_label = model_label
                        reason = "model"

                    results.append({
                        "text": text,
                        "label": final_label,
                        "negative_prob": probs_row[0].item(),
                        "neutral_prob": probs_row[1].item(),
                        "positive_prob": probs_row[2].item(),
                        "confidence": max_prob,
                        "decision": reason
                    })

        return results

    def negative_share(self, texts):
        if not texts:
            return 0, 0

        predictions = self.predict_batch(texts)

        negative = sum(1 for p in predictions if p["label"] == "negative")
        total = len(predictions)

        return negative / total, total
