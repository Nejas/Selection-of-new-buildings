from datetime import datetime
from models import Developer, NewsMention, Project, ReputationData
from parsers import AsyncEISJSParser
from analyzer import SentimentAnalyzer
from db import AsyncSessionLocal
from legal_events import CheckoLegalEventsParser
from news_parser import NewsRSSParser
from news_sources import load_active_news_sources
from repositories import LocalDevelopersRepository, LocalProjectsRepository


class Aggregator:

    def __init__(
        self,
        eis: AsyncEISJSParser | None = None,
        sentiment: SentimentAnalyzer | None = None,
        developers: LocalDevelopersRepository | None = None,
        projects: LocalProjectsRepository | None = None,
        news: NewsRSSParser | None = None,
        legal_events: CheckoLegalEventsParser | None = None,
    ):
        self.eis = eis or AsyncEISJSParser()
        self.sentiment = sentiment
        self.developers = developers or LocalDevelopersRepository()
        self.projects = projects or LocalProjectsRepository()
        self.news = news or NewsRSSParser()
        self.legal_events = legal_events or CheckoLegalEventsParser()

    async def load(self, inn: str, name: str | None = None, reg_date: datetime | None = None):
        profile = self.developers.find_by_inn(inn)
        developer_name = name or (profile.name if profile else f"Застройщик {inn}")
        registration_date = reg_date or (profile.registration_date if profile else None) or datetime.now()

        print(f"\n[Aggregator] Загрузка данных застройщика")
        print(f"   ├─ ИНН: {inn}")
        print(f"   ├─ Имя: {developer_name}")
        print(f"   └─ Дата регистрации: {registration_date}")

        if self.eis.api_key:
            projects = await self.eis.parse(inn)
        else:
            print("[Aggregator] EISJS_API_KEY не задан, внешний источник объектов пропущен")
            projects = []
        if not projects:
            projects = self.projects.find_by_developer_inn(inn)
        if not projects and profile:
            projects = self._projects_from_profile(profile)
        print(f"[Aggregator] Найдено проектов: {len(projects)}")

        legal_events = await self.legal_events.parse(inn)
        print(f"[Aggregator] Найдено правовых событий: {len(legal_events)}")

        reviews = []
        await self._refresh_news_sources()
        news_items = await self.news.parse(developer_name, inn=inn)
        news_texts = [item.text for item in news_items if item.text]
        reputation_texts = reviews + news_texts

        news_mentions = [self._news_mention(item) for item in news_items]

        neutral_news_count = 0
        scored_news_count = 0

        if reputation_texts:
            if self.sentiment is None:
                self.sentiment = SentimentAnalyzer()
            predictions = self.sentiment.predict_batch(reputation_texts)
            news_predictions = predictions[len(reviews):]
            self._apply_news_sentiment(news_mentions, news_predictions)
            stats = self._sentiment_stats(predictions, reviews_count=len(reviews))
            neg_share = stats["negative_share"]
            news_neg_share = stats["negative_news_share"]
            count = stats["scored_texts_count"]
            neutral_news_count = stats["neutral_news_count"]
            scored_news_count = stats["scored_news_count"]
        else:
            neg_share, news_neg_share, count = 0, 0, 0

        print("[Aggregator] Репутационный анализ:")
        print(f"   ├─ Текстов, влияющих на оценку: {count}")
        print(f"   ├─ Новостей: {len(news_texts)}")
        print(f"   ├─ Нейтральных новостей: {neutral_news_count}")
        print(f"   └─ Доля негативных: {neg_share:.2f}")

        rep = ReputationData(
            avg_score=1 - neg_share,
            negative_review_share=neg_share,
            reviews_count=count,
            news_mentions=len(news_texts),
            negative_news_share=news_neg_share,
            neutral_news_count=neutral_news_count,
            scored_news_count=scored_news_count,
        )

        dev = Developer(
            inn=inn,
            name=developer_name,
            registration_date=registration_date,
            projects=projects,
            legal_events=legal_events,
            reputation=rep,
            news_mentions=news_mentions,
        )

        print("[Aggregator] Застройщик собран успешно")
        return dev

    def _projects_from_profile(self, profile) -> list[Project]:
        total_objects = profile.building_objects_count + profile.commissioned_objects_count
        if total_objects == 0 and profile.problem_objects_count == 0:
            return []

        return [
            Project(
                name=f"Портфель объектов: {profile.name}",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=0,
                delay_count=0,
                is_problem=profile.problem_objects_count > 0,
                area=0.0,
            )
        ]

    async def _refresh_news_sources(self):
        try:
            async with AsyncSessionLocal() as session:
                sources = await load_active_news_sources(session)
        except Exception as exc:
            print(f"[Aggregator] Источники новостей из БД недоступны: {exc}")
            return

        if sources:
            self.news.sources = sources

    def _news_mention(self, item) -> NewsMention:
        return NewsMention(
            title=item.title,
            summary=item.summary,
            published_at=item.published_at,
            link=item.link,
        )

    def _apply_news_sentiment(self, mentions: list[NewsMention], predictions: list[dict]):
        for mention, prediction in zip(mentions, predictions):
            mention.sentiment = prediction["label"]

    def _sentiment_stats(self, predictions: list[dict], reviews_count: int = 0) -> dict:
        review_predictions = predictions[:reviews_count]
        news_predictions = predictions[reviews_count:]

        scored_predictions = [
            prediction for prediction in [*review_predictions, *news_predictions]
            if prediction["label"] != "neutral"
        ]
        scored_news_predictions = [
            prediction for prediction in news_predictions
            if prediction["label"] != "neutral"
        ]

        negative_count = sum(
            1 for prediction in scored_predictions
            if prediction["label"] == "negative"
        )
        negative_news_count = sum(
            1 for prediction in scored_news_predictions
            if prediction["label"] == "negative"
        )
        neutral_news_count = sum(
            1 for prediction in news_predictions
            if prediction["label"] == "neutral"
        )

        scored_texts_count = len(scored_predictions)
        scored_news_count = len(scored_news_predictions)

        return {
            "negative_share": negative_count / scored_texts_count if scored_texts_count else 0,
            "negative_news_share": (
                negative_news_count / scored_news_count if scored_news_count else 0
            ),
            "scored_texts_count": scored_texts_count,
            "scored_news_count": scored_news_count,
            "neutral_news_count": neutral_news_count,
        }
