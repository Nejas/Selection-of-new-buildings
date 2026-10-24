"""
Тесты для API endpoints
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from types import SimpleNamespace

from models import Developer, LegalEvent, NewsMention, Project, ReputationData


def test_api_score_endpoint_success(test_client, sample_developer_data, mock_scoring_result):
    """
    Тест успешного запроса к API /api/score/{inn}
    """
    print(" Тест: Успешный запрос к /api/score/{inn}")

    # Мокаем зависимости
    mock_aggregator = AsyncMock()
    mock_developer = AsyncMock()
    mock_developer.name = sample_developer_data["name"]
    mock_developer.registration_date = datetime.strptime(
        sample_developer_data["registration_date"], "%Y-%m-%d"
    )
    mock_aggregator.load.return_value = mock_developer

    mock_scoring = MagicMock()
    mock_scoring.evaluate.return_value = mock_scoring_result

    # Патчим зависимости в основном модуле
    with patch('app.agg', mock_aggregator), \
         patch('app.scoring', mock_scoring):

        client = test_client
        inn = sample_developer_data["inn"]

        response = client.get(f"/api/score/{inn}")

        print(f" Запрос: GET /api/score/{inn}")
        print(f" Ответ: статус {response.status_code}")

        # Проверки
        assert response.status_code == 200

        data = response.json()
        assert data["score"] == mock_scoring_result["score"]
        assert data["status"] == mock_scoring_result["status"]

        print("✅ API вернул корректный результат оценки")


def test_api_invalid_inn_format(test_client):
    """
    Тест невалидного формата ИНН.
    """
    print("\n Тест: Невалидный формат ИНН")

    client = test_client

    # Тест 1: слишком короткий ИНН
    response = client.get("/api/score/123")
    print(f" Короткий ИНН: статус {response.status_code}")
    assert response.status_code != 200

    # Тест 2: нечисловой ИНН
    response = client.get("/api/score/abc")
    print(f" Нечисловой ИНН: статус {response.status_code}")
    assert response.status_code != 200

    print(f"✅ Невалидные ИНН отклонены")


def test_api_score_with_zero_score(test_client, sample_developer_data):
    """
    Тест обработки нулевого рейтинга.
    """
    print("\n Тест: Рейтинг с нулевым score")

    mock_aggregator = AsyncMock()
    mock_developer = AsyncMock()
    mock_developer.name = sample_developer_data["name"]
    mock_developer.registration_date = datetime.strptime(
        sample_developer_data["registration_date"], "%Y-%m-%d"
    )
    mock_aggregator.load.return_value = mock_developer

    zero_result = {
        "score": 0,
        "status": "Высокий риск",
        "details": {}
    }

    mock_scoring = MagicMock()
    mock_scoring.evaluate.return_value = zero_result

    with patch('app.agg', mock_aggregator), \
         patch('app.scoring', mock_scoring):

        client = test_client
        response = client.get(f"/api/score/{sample_developer_data['inn']}")

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0
        assert data["status"] == "Высокий риск"

        print(f"✅ Нулевой рейтинг обработан")


def test_root_endpoint(test_client):
    """Тест корневого endpoint."""
    print("\n Тест: Корневой endpoint")

    client = test_client
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Рейтинг застройщиков" in response.text
    print("✅ Корневой endpoint отдаёт сайт")


def test_health_check(test_client):
    """Тест health check endpoint."""
    print("\n Тест: Health check")

    client = test_client
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    print(f"✅ Health check работает: статус {data['status']}")


# Новый тест: проверка ошибки агрегатора
def test_api_score_aggregator_error(test_client):
    """
    Тест обработки ошибки в Aggregator.
    """
    print("\n Тест: Обработка ошибки Aggregator")

    mock_aggregator = AsyncMock()
    mock_aggregator.load.side_effect = Exception("Ошибка загрузки данных")

    with patch('app.agg', mock_aggregator):
        response = test_client.get("/api/score/7700999999")

        print(f" Запрос с ошибкой Aggregator")
        print(f" Ответ: статус {response.status_code}")

        # Проверяем, что не 200 OK
        assert response.status_code != 200
        print(f"✅ Ошибка обработана, статус {response.status_code}")


def test_api_search_developers(test_client):
    mock_developers_repo = MagicMock()
    mock_developers_repo.search.return_value = [
        SimpleNamespace(
            inn="5050102110",
            name="10 КВАРТАЛ",
            registration_date=datetime(2013, 1, 1),
            region="Московская область",
            problem_objects_count=0,
            building_objects_count=1,
            commissioned_objects_count=18,
        )
    ]

    mock_aggregator = MagicMock()
    mock_aggregator.developers = mock_developers_repo

    with patch("app.agg", mock_aggregator):
        response = test_client.get("/api/developers/search?query=квартал")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["inn"] == "5050102110"
    assert data[0]["name"] == "10 КВАРТАЛ"


def test_api_developer_dossier(test_client):
    mock_aggregator = AsyncMock()
    mock_aggregator.load.return_value = Developer(
        inn="5050102110",
        name="10 КВАРТАЛ",
        registration_date=datetime(2013, 1, 1),
        projects=[
            Project(
                name="ЖК Мечта",
                planned_date=datetime(2021, 12, 31),
                current_planned_date=datetime(2021, 12, 31),
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=5487.8,
            )
        ],
        legal_events=[
            LegalEvent(
                date=datetime(2024, 1, 10),
                event_type="court_case_defendant",
                status="actual",
                source="https://kad.arbitr.ru/Card/1",
                description="Дело А40-1/2024",
            )
        ],
        reputation=ReputationData(
            avg_score=1,
            negative_review_share=0,
            reviews_count=1,
            news_mentions=1,
            negative_news_share=0,
        ),
        news_mentions=[
            NewsMention(
                title="10 КВАРТАЛ построил дом",
                summary="Новость",
                published_at=datetime(2024, 2, 1),
                link="https://example.com/news",
                sentiment="positive",
            )
        ],
    )

    mock_scoring = MagicMock()
    mock_scoring.evaluate.return_value = {
        "developer": "10 КВАРТАЛ",
        "score": 80,
        "status": "Высокая надёжность",
        "details": {},
        "factors": {"inn": "5050102110"},
    }

    with patch("app.agg", mock_aggregator), patch("app.scoring", mock_scoring):
        response = test_client.get("/api/developers/5050102110/dossier")

    assert response.status_code == 200
    data = response.json()
    assert data["projects"][0]["name"] == "ЖК Мечта"
    assert data["legal_events"][0]["event_type"] == "court_case_defendant"
    assert data["news"][0]["sentiment"] == "positive"


def test_api_statistics_overview(test_client):
    mock_aggregator = MagicMock()
    mock_aggregator.developers.statistics.return_value = {"developers_count": 10}
    mock_aggregator.projects.statistics.return_value = {"projects_count": 20}

    with patch("app.agg", mock_aggregator), patch("app.problem_objects_report") as report_repo:
        report_repo.load.return_value = None
        response = test_client.get("/api/statistics/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["developers"]["developers_count"] == 10
    assert data["projects"]["projects_count"] == 20
