from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import httpx

from config import settings
from news_sources import NewsSource


@dataclass(frozen=True)
class NewsItem:
    title: str
    summary: str = ""
    published_at: datetime | None = None
    link: str | None = None

    @property
    def text(self) -> str:
        return " ".join(part for part in (self.title, self.summary) if part).strip()


class NewsRSSParser:
    CONTEXT_WORDS = {
        "застройщик", "девелопер", "жк", "новостройка", "новостройки",
        "строительство", "строит", "построил", "построит", "дом", "жилье",
        "жилой", "жилая", "комплекс", "квартира", "квартиры", "проект",
        "дольщик", "дольщики", "недвижимость", "девелопмент", "эскроу",
        "ипотека", "продажи", "площадь", "метров", "рейтинг",
    }
    GENERIC_NAME_PARTS = {
        "сз", "ооо", "ао", "пао", "зао", "оао", "жк", "жилой", "дом",
        "проект", "группа", "компания", "специализированный", "застройщик",
        "девелопмент", "недвижимость", "объект", "строй", "строительство",
    }

    def __init__(
        self,
        url_template: str | None = None,
        sources: list[NewsSource] | None = None,
        limit: int | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.url_template = url_template or settings.news_rss_url_template
        self.sources = sources
        self.limit = limit or settings.news_limit
        self.client = client or httpx.AsyncClient(timeout=10)

    async def parse(self, developer_name: str, inn: str | None = None) -> list[NewsItem]:
        queries = self._search_queries(developer_name, inn)
        sources = self.sources or [
            NewsSource(
                name="Configured RSS",
                source_type="rss",
                url_template=self.url_template,
                requires_query=True,
            )
        ]

        print(f"[News] Поиск новостей: {developer_name}")

        all_items = []
        for source in sources:
            if source.source_type != "rss":
                continue

            source_queries = queries if source.requires_query or "{query}" in source.url_template else [None]
            for query in source_queries:
                url = self._source_url(source, query)
                try:
                    response = await self.client.get(url)
                    response.raise_for_status()
                    all_items.extend(self._parse_rss(response.text))
                except Exception as exc:
                    print(f"[News] Ошибка RSS {source.name}: {exc}")

        return self._deduplicate(
            self._filter_relevant(all_items, developer_name, inn)
        )[: self.limit]

    def _parse_rss(self, xml_text: str) -> list[NewsItem]:
        root = ET.fromstring(xml_text)
        items = []

        for item in root.findall(".//item"):
            title = self._child_text(item, "title")
            if not title:
                continue

            items.append(
                NewsItem(
                    title=title,
                    summary=self._child_text(item, "description"),
                    published_at=self._parse_date(self._child_text(item, "pubDate")),
                    link=self._child_text(item, "link") or None,
                )
            )

        print(f"[News] Найдено новостей: {len(items)}")
        return items

    def _filter_relevant(
        self,
        items: list[NewsItem],
        developer_name: str,
        inn: str | None = None,
    ) -> list[NewsItem]:
        normalized_names = [self._normalize(alias) for alias in self._developer_aliases(developer_name)]
        normalized_inn = self._normalize(inn or "")
        relevant = []

        for item in items:
            text = self._normalize(item.text)
            if normalized_inn and normalized_inn in text:
                relevant.append(item)
                continue
            if self._matches_developer_name(text, normalized_names):
                relevant.append(item)

        print(f"[News] Релевантных новостей: {len(relevant)}")
        return relevant

    def _source_url(self, source: NewsSource, query: str | None) -> str:
        if source.requires_query or "{query}" in source.url_template:
            return source.url_template.format(query=query or "")
        return source.url_template

    def _search_queries(self, developer_name: str, inn: str | None = None) -> list[str]:
        queries = []
        for alias in self._developer_aliases(developer_name):
            queries.append(quote_plus(f'"{alias}" застройщик'))
            queries.append(quote_plus(f'"{alias}"'))

        if inn:
            queries.append(quote_plus(str(inn)))

        return list(dict.fromkeys(queries))

    def _developer_aliases(self, developer_name: str) -> list[str]:
        aliases = [developer_name.strip()]
        clean = re.sub(
            r"\b(ооо|ао|пао|зао|оао|сз|специализированный|застройщик|гк|группа|компаний)\b",
            " ",
            developer_name,
            flags=re.IGNORECASE,
        )
        clean = re.sub(r"\s+", " ", clean).strip(" «»\"'")
        if clean and clean not in aliases:
            aliases.append(clean)

        aliases.extend(self._brand_parts(clean))
        return aliases

    def _brand_parts(self, clean_name: str) -> list[str]:
        parts = re.split(r"[\s.,;:/\\|()«»\"'№#-]+", clean_name)
        brands = []
        for part in parts:
            normalized = self._normalize(part)
            if len(normalized) < 3 or normalized in self.GENERIC_NAME_PARTS:
                continue
            if normalized.isdigit():
                continue
            brands.append(part)
        return list(dict.fromkeys(brands))[:3]

    def _matches_developer_name(self, text: str, names: list[str]) -> bool:
        if not names:
            return False

        full_name = names[0]
        if full_name and full_name in text:
            return True

        has_context = any(word in text for word in self.CONTEXT_WORDS)
        return has_context and any(name and name in text for name in names[1:])

    def _deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        seen = set()
        unique = []
        for item in items:
            key = item.link or item.title
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _normalize(self, value: str) -> str:
        value = value.lower().replace("ё", "е")
        value = re.sub(r"[^0-9a-zа-я]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def _child_text(self, item: ET.Element, tag: str) -> str:
        child = item.find(tag)
        return (child.text or "").strip() if child is not None else ""

    def _parse_date(self, value: str) -> datetime | None:
        if not value:
            return None
        try:
            return parsedate_to_datetime(value)
        except Exception:
            return None
