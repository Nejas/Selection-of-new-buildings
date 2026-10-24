import pytest
import numpy as np
from scoring import TopsisCalculator
from models import Developer, Project, ReputationData
from datetime import datetime


def test_topsis_result_range():
    """
    Тест проверяет, что метод compute_score возвращает значение
    в правильном диапазоне (0-100) или None
    """
    print("Тест: test_topsis_result_range")
    print("Проверяем, что оценка TOPSIS находится в диапазоне 0-100")

    # Создаем тестового застройщика
    dev = Developer(
        inn="123",
        name="Тест",
        registration_date=datetime(2015, 1, 1),  # Более 1 года назад
        projects=[
            Project(
                name="Проект 1",
                planned_date=datetime(2023, 1, 1),
                current_planned_date=datetime(2023, 1, 1),
                delay_days_avg=0,
                delay_count=0,
                is_problem=False,
                area=1000
            ),
            Project(
                name="Проект 2",
                planned_date=datetime(2023, 6, 1),
                current_planned_date=datetime(2023, 8, 1),
                delay_days_avg=60,
                delay_count=1,
                is_problem=False,
                area=2000
            )
        ],
        legal_events=[],  # Нет юридических событий
        reputation=ReputationData(
            avg_score=0.8,
            negative_review_share=0.2,
            reviews_count=50,  # Более 20 отзывов
            news_mentions=5,
            negative_news_share=0.3
        )
    )

    print(f"✅ Создан тестовый застройщик: {dev.name}")
    print(f"   ИНН: {dev.inn}")
    print(f"   Дата регистрации: {dev.registration_date}")
    print(f"   Количество проектов: {len(dev.projects)}")
    print(f"   Количество отзывов: {dev.reputation.reviews_count if dev.reputation else 0}")

    calculator = TopsisCalculator()
    print("✅ Создан экземпляр TopsisCalculator")

    score = calculator.compute_score(dev)
    print(f"✅ Рассчитана оценка: {score}")

    # Проверяем, что score - это число или None
    assert score is None or isinstance(score, (int, float))
    print(f"✅ Проверка типа данных пройдена: score является {type(score).__name__}")

    # Если score не None, проверяем диапазон
    if score is not None:
        assert 0 <= score <= 100  # Ваш метод возвращает score * 100
        print(f"✅ Проверка диапазона пройдена: {score} находится в диапазоне 0-100")
    else:
        print(" Score = None (неизвестный застройщик)")

    print("Тест test_topsis_result_range завершен успешно!\n")


def test_topsis_unknown_developer():
    """
    Тест для застройщика с недостаточными данными.
    Должен вернуть None, так как критерии неизвестны.
    """
    print("Тест: test_topsis_unknown_developer")
    print("Проверяем, что для нового застройщика возвращается None")

    dev = Developer(
        inn="456",
        name="Новый застройщик",
        registration_date=datetime(2024, 1, 1),  # Менее 1 года
        projects=[],  # Нет проектов
        legal_events=[],
        reputation=None  # Нет данных о репутации
    )

    print(f"✅ Создан новый застройщик с минимальными данными:")
    print(f"   ИНН: {dev.inn}")
    print(f"   Имя: {dev.name}")
    print(f"   Дата регистрации: {dev.registration_date} (менее 1 года)")
    print(f"   Количество проектов: {len(dev.projects)}")
    print(f"   Данные репутации: {'отсутствуют' if dev.reputation is None else 'есть'}")

    calculator = TopsisCalculator()
    score = calculator.compute_score(dev)

    print(f"✅ Рассчитана оценка: {score}")

    # Должен вернуть None для неизвестного застройщика
    assert score is None

    if score is None:
        print("✅ Тест пройден: для нового застройщика вернулся None")
    else:
        print(f" Внимание: для нового застройщика вернулось значение {score}")

    print(" Тест test_topsis_unknown_developer завершен успешно!\n")