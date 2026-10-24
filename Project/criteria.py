from typing import Optional
from datetime import datetime
import math

from models import Developer


class DeadlineDiscipline:

    def score(self, dev: Developer) -> Optional[float]:
        if not dev.projects:
            return None

        total_area = sum(p.area for p in dev.projects if p.area > 0)
        if total_area > 0:
            avg_delay = sum(p.delay_days_avg * p.area for p in dev.projects) / total_area
        else:
            delays = [p.delay_days_avg for p in dev.projects]
            avg_delay = sum(delays) / len(delays)

        score = 1 - min(avg_delay / 365, 1)

        return max(0, min(1, score))


class ProblemObjects:

    def score(self, dev: Developer) -> Optional[float]:
        if not dev.projects:
            return None
        return 0.0 if any(p.is_problem for p in dev.projects) else 1.0


class LegalRisk:
    PENALTIES = {
        "court_case_defendant": 0.18,
        "court_case_participant": 0.12,
        "court_case_plaintiff": 0.06,
        "bankruptcy": 0.60,
        "administrative_penalty": 0.25,
        "construction_stopped": 0.45,
    }
    HALF_LIFE_YEARS = 3

    def score(self, dev: Developer) -> Optional[float]:
        if not dev.legal_events:
            return None

        total_penalty = sum(self._event_penalty(event) for event in dev.legal_events)
        score = 1 - min(total_penalty, 1)
        return max(0, min(1, score))

    def _event_penalty(self, event) -> float:
        base = self.PENALTIES.get(event.event_type, 0.10)
        if event.status == "active":
            base *= 1.25

        age_years = max((datetime.now() - event.date).days / 365, 0)
        decay = math.pow(0.5, age_years / self.HALF_LIFE_YEARS)
        return base * decay


class ReputationRisk:

    def score(self, dev: Developer) -> Optional[float]:
        r = dev.reputation
        if r is None or r.reviews_count < 20:
            return None

        score = 1 - (0.6*r.negative_review_share + 0.4*r.negative_news_share)

        return max(0, min(1, score))
