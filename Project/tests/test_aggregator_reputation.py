from aggregator import Aggregator


def test_sentiment_stats_excludes_neutral_news_from_score():
    aggregator = Aggregator.__new__(Aggregator)
    predictions = [
        {"label": "negative"},
        {"label": "neutral"},
        {"label": "positive"},
        {"label": "neutral"},
    ]

    stats = aggregator._sentiment_stats(predictions, reviews_count=0)

    assert stats["neutral_news_count"] == 2
    assert stats["scored_news_count"] == 2
    assert stats["scored_texts_count"] == 2
    assert stats["negative_news_share"] == 0.5
    assert stats["negative_share"] == 0.5


def test_sentiment_stats_all_neutral_news_do_not_affect_score():
    aggregator = Aggregator.__new__(Aggregator)
    predictions = [
        {"label": "neutral"},
        {"label": "neutral"},
    ]

    stats = aggregator._sentiment_stats(predictions, reviews_count=0)

    assert stats["neutral_news_count"] == 2
    assert stats["scored_news_count"] == 0
    assert stats["scored_texts_count"] == 0
    assert stats["negative_news_share"] == 0
    assert stats["negative_share"] == 0
