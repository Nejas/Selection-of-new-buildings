from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models_db import NewsSourceDB


@dataclass(frozen=True)
class NewsSource:
    name: str
    source_type: str
    url_template: str
    requires_query: bool = False


DEFAULT_NEWS_SOURCES = [
    NewsSource(
        name="Google News RSS",
        source_type="rss",
        url_template=settings.news_rss_url_template,
        requires_query=True,
    ),
    NewsSource(
        name="Ведомости Недвижимость",
        source_type="rss",
        url_template="https://www.vedomosti.ru/rss/rubric/realty",
        requires_query=False,
    ),
    NewsSource(
        name="Ведомости Жилая недвижимость",
        source_type="rss",
        url_template="https://www.vedomosti.ru/rss/rubric/realty/housing",
        requires_query=False,
    ),
]


async def seed_default_news_sources(session: AsyncSession):
    for source in DEFAULT_NEWS_SOURCES:
        result = await session.execute(
            select(NewsSourceDB).where(NewsSourceDB.name == source.name)
        )
        if result.scalar_one_or_none():
            continue

        session.add(
            NewsSourceDB(
                name=source.name,
                source_type=source.source_type,
                url_template=source.url_template,
                requires_query=source.requires_query,
                is_active=True,
            )
        )

    await session.commit()


async def load_active_news_sources(session: AsyncSession) -> list[NewsSource]:
    result = await session.execute(
        select(NewsSourceDB)
        .where(NewsSourceDB.is_active.is_(True))
        .order_by(NewsSourceDB.id)
    )

    return [
        NewsSource(
            name=row.name,
            source_type=row.source_type,
            url_template=row.url_template,
            requires_query=row.requires_query,
        )
        for row in result.scalars().all()
    ]
