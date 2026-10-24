from datetime import datetime
from criteria import *
from models import Developer


class TopsisCalculator:

    def __init__(self):
        self.criteria = [
            DeadlineDiscipline(),
            ProblemObjects(),
            LegalRisk(),
            ReputationRisk()
        ]
        self.weights = [0.40, 0.25, 0.20, 0.15]

    def unknown(self, dev: Developer):
        if len(dev.projects) == 0:
            return True
        if (datetime.now() - dev.registration_date).days < 365:
            return True
        return False

    def unknown_reasons(self, dev: Developer):
        reasons = []
        if len(dev.projects) == 0:
            reasons.append("Нет данных об объектах застройщика")
        if (datetime.now() - dev.registration_date).days < 365:
            reasons.append("Застройщик зарегистрирован менее года назад")
        return reasons

    def data_warnings(self, dev: Developer):
        warnings = []
        if not dev.reputation:
            warnings.append("Нет данных о репутации")
        elif dev.reputation.reviews_count < 20:
            warnings.append("Недостаточно репутационных текстов для устойчивой оценки")
        if not dev.legal_events:
            warnings.append("Негативные судебные дела по этому ИНН не найдены")
        return warnings

    def criteria_scores(self, dev: Developer):
        return {
            "deadline_discipline": self.criteria[0].score(dev),
            "problem_objects": self.criteria[1].score(dev),
            "legal_risk": self.criteria[2].score(dev),
            "reputation_risk": self.criteria[3].score(dev),
        }

    def compute_score(self, dev: Developer):
        print("\n [TOPSIS] Расчёт рейтинга")

        if self.unknown(dev):
            print(" [TOPSIS] Недостаточно данных -> score=None")
            return None

        scores = [c.score(dev) for c in self.criteria]
        print(f"   Частные оценки: {scores}")

        scores = [0.5 if s is None else s for s in scores]
        weighted = [s * w for s, w in zip(scores, self.weights)]
        total = sum(weighted)

        print(f"   Итоговый score: {total * 100:.2f}")
        return total * 100


class StatusAssigner:

    def status_from_score(self, score, has_problem, avg_delay_days=None):
        # 1. Неизвестный
        if score is None:
            return "Неизвестный"

        # 2. Проблемный объект = высокий риск при низком балле
        if has_problem and score < 60:
            return "Высокий риск"

        # 3. Ограничение сверху при проблемном объекте
        if has_problem and score >= 60:
            base_status = "Рискованный"
        else:
            # 4. Базовый статус по score
            if score >= 80:
                base_status = "Высокая надёжность"
            elif score >= 60:
                base_status = "Средняя надёжность"
            elif score >= 40:
                base_status = "Рискованный"
            else:
                base_status = "Высокий риск"

        # 5.  ДЕГРАДАЦИЯ ПРИ КРИТИЧЕСКИХ ЗАДЕРЖКАХ
        if avg_delay_days is not None and avg_delay_days > 180:
            if base_status == "Высокая надёжность":
                return "Средняя надёжность"
            if base_status == "Средняя надёжность":
                return "Рискованный"
            if base_status == "Рискованный":
                return "Высокий риск"

        return base_status


class ScoringService:
    def __init__(self):
        self.topsis = TopsisCalculator()
        self.assigner = StatusAssigner()

    def evaluate(self, dev: Developer):
        score = self.topsis.compute_score(dev)
        has_problem = any(p.is_problem for p in dev.projects)
        avg_delay = None
        if dev.projects:
            avg_delay = sum(p.delay_days_avg for p in dev.projects) / len(dev.projects)

        status = self.assigner.status_from_score(score, has_problem, avg_delay)

        print("[Scoring] Результат:")
        print(f"   ├─ Score: {score}")
        print(f"   └─ Status: {status}")

        return {
            "developer": dev.name,
            "score": None if score is None else round(score, 2),
            "status": status,
            "details": self._details(dev),
            "factors": self._factors(dev, avg_delay, has_problem),
        }

    def _details(self, dev: Developer):
        return {
            "criteria": self.topsis.criteria_scores(dev),
            "weights": {
                "deadline_discipline": self.topsis.weights[0],
                "problem_objects": self.topsis.weights[1],
                "legal_risk": self.topsis.weights[2],
                "reputation_risk": self.topsis.weights[3],
            },
            "unknown_reasons": self.topsis.unknown_reasons(dev),
            "data_warnings": self.topsis.data_warnings(dev),
        }

    def _factors(self, dev: Developer, avg_delay, has_problem):
        reputation = dev.reputation
        return {
            "inn": dev.inn,
            "registration_date": dev.registration_date.date().isoformat(),
            "projects_count": len(dev.projects),
            "problem_projects_count": sum(1 for p in dev.projects if p.is_problem),
            "delayed_projects_count": sum(1 for p in dev.projects if p.delay_count > 0),
            "has_problem_objects": has_problem,
            "avg_delay_days": avg_delay,
            "legal_events_count": len(dev.legal_events),
            "reviews_count": reputation.reviews_count if reputation else 0,
            "news_mentions": reputation.news_mentions if reputation else 0,
            "neutral_news_count": reputation.neutral_news_count if reputation else 0,
            "scored_news_count": reputation.scored_news_count if reputation else 0,
            "negative_review_share": reputation.negative_review_share if reputation else None,
            "negative_news_share": reputation.negative_news_share if reputation else None,
        }
