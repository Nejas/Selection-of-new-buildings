from news_sources import DEFAULT_NEWS_SOURCES


def test_default_news_sources_include_search_and_plain_feeds():
    assert any(source.requires_query for source in DEFAULT_NEWS_SOURCES)
    assert any(not source.requires_query for source in DEFAULT_NEWS_SOURCES)
    assert all(source.source_type == "rss" for source in DEFAULT_NEWS_SOURCES)
