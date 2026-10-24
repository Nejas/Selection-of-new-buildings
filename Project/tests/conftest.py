import sys
import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Добавляем корневую директорию в путь Python
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Импортируем приложение ПОСЛЕ добавления пути
try:
    from app import app
except ImportError as e:
    print(f"Ошибка импорта app.app: {e}. Проверьте app.py")
    raise


@pytest.fixture(scope="session")
def event_loop():
    """Event loop для async-тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Фикстура TestClient для FastAPI."""
    print("✅ Фикстура test_client создана")
    return TestClient(app)


@pytest.fixture
def sample_developer_data():
    return {
        "inn": "7700123450",
        "name": "ООО АльфаСтрой",
        "registration_date": "2020-05-10"
    }


@pytest.fixture
def mock_scoring_result():
    return {
        "score": 85.5,
        "status": "Высокая надёжность",
        "details": {
            "criteria_1": 0.95,
            "criteria_2": 0.98,
            "criteria_3": 0.87,
            "criteria_4": 0.72
        }
    }
