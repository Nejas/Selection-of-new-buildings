from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Project:
    name: str
    planned_date: datetime
    current_planned_date: datetime
    delay_days_avg: float
    delay_count: int
    is_problem: bool
    area: float


@dataclass
class LegalEvent:
    date: datetime
    event_type: str
    status: str
    source: str = ""
    description: str = ""


@dataclass
class ReputationData:
    avg_score: float
    negative_review_share: float
    reviews_count: int
    news_mentions: int
    negative_news_share: float
    neutral_news_count: int = 0
    scored_news_count: int = 0


@dataclass
class NewsMention:
    title: str
    summary: str = ""
    published_at: datetime | None = None
    link: str | None = None
    sentiment: str | None = None


@dataclass
class Developer:
    inn: str
    name: str
    registration_date: datetime
    projects: List[Project] = field(default_factory=list)
    legal_events: List[LegalEvent] = field(default_factory=list)
    reputation: Optional[ReputationData] = None
    news_mentions: List[NewsMention] = field(default_factory=list)
