import pytest

from news_parser import NewsRSSParser
from news_sources import NewsSource


def test_news_rss_parser_extracts_items_from_rss():
    parser = NewsRSSParser(limit=10)
    xml = """
    <rss>
      <channel>
        <item>
          <title>Застройщик построил новый дом</title>
          <description>Краткое описание новости</description>
          <pubDate>Fri, 08 Oct 2021 10:00:00 GMT</pubDate>
          <link>https://example.com/news</link>
        </item>
      </channel>
    </rss>
    """

    items = parser._parse_rss(xml)

    assert len(items) == 1
    assert items[0].title == "Застройщик построил новый дом"
    assert items[0].summary == "Краткое описание новости"
    assert items[0].published_at.year == 2021
    assert items[0].link == "https://example.com/news"
    assert "Краткое описание" in items[0].text


def test_news_rss_parser_filters_irrelevant_items():
    parser = NewsRSSParser(limit=10)
    items = [
        parser_item("ПИК построил новый дом", "ИНН 7713011336"),
        parser_item("Новости квартала", "Без упоминания компании"),
    ]

    relevant = parser._filter_relevant(items, "ПИК", inn="7713011336")

    assert len(relevant) == 1
    assert relevant[0].title == "ПИК построил новый дом"


def test_news_rss_parser_filters_by_clean_developer_name():
    parser = NewsRSSParser(limit=10)
    items = [
        parser_item("Компания Самолет открыла продажи", "Проект застройщика"),
        parser_item("Новости авиации", "Самолет вылетел из Москвы"),
    ]

    relevant = parser._filter_relevant(items, "СЗ Самолет")

    assert len(relevant) == 1
    assert relevant[0].title == "Компания Самолет открыла продажи"


def test_news_rss_parser_builds_queries_by_name_and_inn():
    parser = NewsRSSParser()

    queries = parser._search_queries("СЗ Самолет", inn="9731000000")

    assert any("%D0%A1%D0%B0%D0%BC%D0%BE%D0%BB%D0%B5%D1%82" in query for query in queries)
    assert "9731000000" in queries


def test_news_rss_parser_adds_brand_alias_from_compound_name():
    parser = NewsRSSParser()

    aliases = parser._developer_aliases("СЗ САМОЛЕТ-АЛХИМОВО")

    assert "САМОЛЕТ" in aliases


def test_news_rss_parser_builds_source_urls():
    parser = NewsRSSParser()
    query_source = NewsSource(
        name="Search",
        source_type="rss",
        url_template="https://example.com/rss?q={query}",
        requires_query=True,
    )
    plain_source = NewsSource(
        name="Feed",
        source_type="rss",
        url_template="https://example.com/rss",
        requires_query=False,
    )

    assert parser._source_url(query_source, "pik") == "https://example.com/rss?q=pik"
    assert parser._source_url(plain_source, "pik") == "https://example.com/rss"


def test_news_rss_parser_deduplicates_items():
    parser = NewsRSSParser()
    items = [
        parser_item("Новость", "Описание", link="https://example.com/1"),
        parser_item("Новость дубль", "Описание", link="https://example.com/1"),
    ]

    unique = parser._deduplicate(items)

    assert len(unique) == 1


@pytest.mark.asyncio
async def test_news_rss_parser_returns_empty_list_on_network_error():
    class FailingClient:
        async def get(self, url):
            raise RuntimeError("network error")

    parser = NewsRSSParser(client=FailingClient())

    items = await parser.parse("ТестСтрой")

    assert items == []


def parser_item(title, summary, link=None):
    from news_parser import NewsItem

    return NewsItem(title=title, summary=summary, link=link)
