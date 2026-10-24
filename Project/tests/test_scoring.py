import pytest
from scoring import ScoringService
from models import Developer, LegalEvent, Project, ReputationData
from datetime import datetime, timedelta


@pytest.fixture
def service():
    print("  Создание фикстуры: инициализация ScoringService")
    return ScoringService()

def test_scoring_high_reliability():
    scoring = ScoringService()

    dev = make_developer(
        name="НадёжСтрой",
        reg_years_ago=5,
        reviews_count=100,
        negative_share=0.05,
        projects=[
            Project(
                name="Дом А",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=5,
                delay_count=0,
                is_problem=False,
                area=10000
            )
        ]
    )

    result = scoring.evaluate(dev)
    print("\n High reliability:", result)

    assert result["status"] == "Высокая надёжность"


def test_scoring_medium_reliability():
    scoring = ScoringService()

    dev = make_developer(
        name="СтабилСтрой",
        reg_years_ago=4,
        reviews_count=60,
        negative_share=0.25,
        projects=[
            Project(
                name="Дом B",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=90,
                delay_count=2,
                is_problem=False,
                area=8000
            )
        ]
    )

    result = scoring.evaluate(dev)
    print("\n Medium reliability:", result)

    assert result["status"] == "Средняя надёжность"


def test_scoring_risky():
    scoring = ScoringService()

    dev = make_developer(
        name="РискСтрой",
        reg_years_ago=6,
        reviews_count=40,
        negative_share=0.45,
        projects=[
            Project(
                name="Дом C",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=200,
                delay_count=5,
                is_problem=False,
                area=6000
            )
        ]
    )

    result = scoring.evaluate(dev)
    print("\n Risky:", result)

    assert result["status"] == "Рискованный"

def test_scoring_high_risk():
    scoring = ScoringService()

    dev = make_developer(
        name="ПроблемСтрой",
        reg_years_ago=7,
        reviews_count=80,
        negative_share=0.30,
        projects=[
            Project(
                name="Дом D",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=150,
                delay_count=10,
                is_problem=True,
                area=7000
            )
        ]
    )

    result = scoring.evaluate(dev)
    print("\n High risk:", result)

    assert result["status"] == "Высокий риск"

def test_scoring_unknown_developer():
    scoring = ScoringService()

    dev = make_developer(
        name="НовыйСтрой",
        reg_years_ago=0,
        reviews_count=5,
        negative_share=0.1,
        projects=[]
    )

    result = scoring.evaluate(dev)
    print("\n Unknown:", result)

    assert result["status"] == "Неизвестный"
    assert result["score"] is None
    assert "unknown_reasons" in result["details"]


def make_developer(
    *,
    name: str,
    projects: list,
    reviews_count: int,
    negative_share: float,
    reg_years_ago: int
):
    return Developer(
        inn="9999999999",
        name=name,
        registration_date=datetime.now() - timedelta(days=365 * reg_years_ago),
        projects=projects,
        legal_events=[],
        reputation=ReputationData(
            avg_score=1 - negative_share,
            negative_review_share=negative_share,
            reviews_count=reviews_count,
            news_mentions=0,
            negative_news_share=0
        )
    )

def test_scoring_basic(service):
    """
    Тест базовой функциональности скоринговой системы
    """
    print(" Тест: test_scoring_basic")
    print("Проверяем базовую работу сервиса оценки застройщиков")

    dev = Developer(
        inn="123",
        name="ТестСтрой",
        registration_date=datetime(2020, 1, 1),
        projects=[
            Project(
                name="Дом 1",
                planned_date=datetime(2023, 1, 1),
                current_planned_date=datetime(2023, 1, 1),
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=5000
            )
        ],
        legal_events=[],
        reputation=ReputationData(
            avg_score=0.9,
            negative_review_share=0.1,
            reviews_count=10,
            news_mentions=3,
            negative_news_share=0.1
        )
    )

    print(f"✅ Создан тестовый застройщик:")
    print(f"   Имя: {dev.name}")
    print(f"   ИНН: {dev.inn}")
    print(f"   Проектов: {len(dev.projects)}")
    print(f"   Средняя оценка репутации: {dev.reputation.avg_score}")
    print(f"   Проект: {dev.projects[0].name} ({dev.projects[0].area} м²)")

    result = service.evaluate(dev)

    print(f"\n Результаты оценки:")
    print(f"   Застройщик: {result['developer']}")
    print(f"   Оценка (score): {result['score']}")
    print(f"   Статус: {result['status']}")

    # Используйте правильные статусы из вашего StatusAssigner
    valid_statuses = ("Высокая надёжность", "Средняя надёжность",
                      "Рискованный", "Высокий риск", "Неизвестный")

    print(f"\n Проверяем, что статус находится в допустимом списке:")
    print(f"   Допустимые статусы: {valid_statuses}")
    print(f"   Полученный статус: {result['status']}")

    assert result["status"] in valid_statuses
    print(f"✅ Статус '{result['status']}' корректен")

    # Проверяем score - может быть None или число
    if result["score"] is not None:
        print(f"\n🔍 Проверяем диапазон оценки:")
        print(f"   Оценка: {result['score']}")
        print(f"   Проверка: 0 <= {result['score']} <= 100")

        assert 0 <= result["score"] <= 100
        print(f"✅ Оценка {result['score']} находится в диапазоне 0-100")
    else:
        print("  Score = None (неизвестный застройщик)")

    print("\n Итоговые результаты:")
    print(f"   Статус: {result['status']}")
    print(f"   Оценка: {result['score']}")


def test_scoring_returns_details_and_factors():
    scoring = ScoringService()
    dev = make_developer(
        name="ФакторСтрой",
        reg_years_ago=5,
        reviews_count=30,
        negative_share=0.2,
        projects=[
            Project(
                name="Дом",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=10,
                delay_count=1,
                is_problem=False,
                area=1000,
            )
        ],
    )

    result = scoring.evaluate(dev)

    assert "details" in result
    assert "factors" in result
    assert result["details"]["weights"]["deadline_discipline"] == 0.40
    assert result["details"]["criteria"]["deadline_discipline"] is not None
    assert result["factors"]["projects_count"] == 1
    assert result["factors"]["delayed_projects_count"] == 1
    assert result["factors"]["reviews_count"] == 30


def test_scoring_does_not_block_on_low_reputation_count():
    scoring = ScoringService()

    dev = make_developer(
        name="МалоОтзывовСтрой",
        reg_years_ago=5,
        reviews_count=0,
        negative_share=0,
        projects=[
            Project(
                name="Дом",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=1000,
            )
        ],
    )

    result = scoring.evaluate(dev)

    assert result["score"] is not None
    assert result["status"] != "Неизвестный"
    assert result["details"]["unknown_reasons"] == []
    assert result["details"]["data_warnings"]


def test_deadline_discipline_uses_area_weighted_delay():
    scoring = ScoringService()
    dev = make_developer(
        name="ВесСтрой",
        reg_years_ago=5,
        reviews_count=30,
        negative_share=0.1,
        projects=[
            Project(
                name="Большой дом",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=365,
                delay_count=1,
                is_problem=False,
                area=9000,
            ),
            Project(
                name="Малый дом",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=1000,
            ),
        ],
    )

    criteria = scoring.topsis.criteria_scores(dev)

    assert round(criteria["deadline_discipline"], 2) == 0.10


def test_legal_risk_penalizes_defendant_cases():
    scoring = ScoringService()
    dev = make_developer(
        name="ЮрСтрой",
        reg_years_ago=5,
        reviews_count=30,
        negative_share=0.1,
        projects=[
            Project(
                name="Дом",
                planned_date=None,
                current_planned_date=None,
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=1000,
            )
        ],
    )
    dev.legal_events = [
        LegalEvent(
            date=datetime.now(),
            event_type="court_case_defendant",
            status="actual",
        )
    ]

    criteria = scoring.topsis.criteria_scores(dev)

    assert criteria["legal_risk"] < 1

