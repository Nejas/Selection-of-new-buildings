"""
Тесты для анализатора тональности SentimentAnalyzer
"""

import pytest
import torch
from unittest.mock import patch, MagicMock
from analyzer import SentimentAnalyzer


def test_sentiment_domain_negative_news_overrides_model_label():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = (
        "ФАС возбудила дело против группы «ПИК» из-за монополизации "
        "интернета в новых домах"
    )

    assert sa._keyword_correction(text) == "negative"


def test_sentiment_domain_negative_words_do_not_match_inside_safe_words():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    assert sa._keyword_correction("Новый фасад жилого комплекса готов") is None


def test_sentiment_corporate_ownership_news_is_neutral():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = "Структура группы ПИК увеличила долю в капитале ПИК СЗ до 21,9%"

    assert sa._keyword_correction(text) == "neutral"


def test_sentiment_negative_pattern_has_priority_over_neutral_words():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = "ФАС возбудила дело против группы ПИК из-за монополизации интернета"

    assert sa._keyword_correction(text) == "negative"


def test_sentiment_new_residential_project_news_is_positive():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = (
        "На месте здания Газпрома на юго-западе Москвы появится жилой комплекс. "
        "Его строительством будет заниматься структура группы ПИК"
    )

    assert sa._keyword_correction(text) == "positive"


def test_sentiment_krt_project_news_is_positive():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = (
        "Региональный девелопер Unikey поучаствует в программе КРТ в Москве. "
        "Он вместе с группой ПИК построит многофункциональный центр"
    )

    assert sa._keyword_correction(text) == "positive"


def test_sentiment_non_core_asset_sale_news_is_neutral():
    sa = SentimentAnalyzer.__new__(SentimentAnalyzer)

    text = (
        "ГК ПИК, похоже, продала торговый центр Ома в Очаково-Матвеевском. "
        "Жилые девелоперы все чаще избавляются от непрофильных активов"
    )

    assert sa._keyword_correction(text) == "neutral"


def test_sentiment_negative_share():
    """
    Тест анализатора тональности: проверяем расчет доли негативных отзывов
    """
    print(" Тест: test_sentiment_negative_share")
    print("Проверяем работу анализатора тональности текстов")

    # Создаём анализатор
    sa = SentimentAnalyzer()
    print("✅ Создан экземпляр SentimentAnalyzer")

    # Тестовые тексты
    texts = [
        "Все было плохо, задержки и брак",
        "Отличный дом, доволен покупкой"
    ]

    print(f"\n Тестовые тексты:")
    for i, text in enumerate(texts, 1):
        print(f"   {i}. '{text[:30]}...'")

    print("\n🔍 Анализируем тональность...")
    neg_share, total = sa.negative_share(texts)

    print(f"✅ Результаты анализа:")
    print(f"   Всего текстов: {total}")
    print(f"   Доля негативных: {neg_share:.2f} ({neg_share * 100:.1f}%)")

    print(f"\n Проверяем условия:")
    print(f"   total == 2: {total} == 2")
    print(f"   0 <= neg_share <= 1: 0 <= {neg_share:.2f} <= 1")

    assert total == 2
    assert 0 <= neg_share <= 1

    print(f"\n✅ Проверки пройдены:")
    print(f"   Количество текстов корректно: {total}")
    print(f"   Доля негативных в диапазоне: {neg_share:.2f}")

    print("Тест test_sentiment_negative_share завершен успешно!\n")


def test_sentiment_empty_list():
    """
    Тест анализатора с пустым списком текстов
    """
    print("\n Тест: test_sentiment_empty_list")
    print("Проверяем обработку пустого списка текстов")

    sa = SentimentAnalyzer()

    # Пустой список
    neg_share, total = sa.negative_share([])

    print(f"✅ Результаты для пустого списка:")
    print(f"   Доля негативных: {neg_share:.2f}")
    print(f"   Всего текстов: {total}")

    assert neg_share == 0
    assert total == 0

    print("✅ Пустой список обработан корректно")


def test_sentiment_all_negative():
    """
    Тест анализатора со всеми негативными отзывами
    """
    print("\n Тест: test_sentiment_all_negative")
    print("Проверяем анализ всех негативных текстов")

    # Мокаем модель для контролируемого теста
    mock_model = MagicMock()

    # Создаём моковые предсказания (все негативные)
    mock_outputs = MagicMock()
    mock_logits = torch.tensor([
        [2.0, 0.5, 0.3],  # Первый текст: негативный (индекс 0 имеет наибольшее значение)
        [1.8, 0.7, 0.2],  # Второй текст: негативный
        [2.1, 0.4, 0.3]  # Третий текст: негативный
    ])
    mock_outputs.logits = mock_logits

    mock_model.return_value = mock_outputs
    mock_model.eval = MagicMock()
    mock_model.to = MagicMock(return_value=mock_model)

    with patch('analyzer.AutoModelForSequenceClassification.from_pretrained',
               return_value=mock_model):
        with patch('analyzer.AutoTokenizer.from_pretrained'):
            sa = SentimentAnalyzer()

            # Тестовые тексты (все негативные)
            texts = [
                "Ужасный сервис, никогда больше",
                "Долгострои, обман дольщиков",
                "Плохое качество материалов"
            ]

            neg_share, total = sa.negative_share(texts)

            print(f"✅ Результаты для всех негативных:")
            print(f"   Доля негативных: {neg_share:.2f} (ожидается 1.00)")
            print(f"   Всего текстов: {total}")

            assert neg_share == 1.0  # 100% негативных
            assert total == 3

    print("✅ Все негативные тексты определены корректно")


def test_sentiment_all_positive():
    """
    Тест анализатора со всеми позитивными отзывами
    """
    print("\n Тест: test_sentiment_all_positive")
    print("Проверяем анализ всех позитивных текстов")

    # Мокаем модель
    mock_model = MagicMock()

    # Создаём моковые предсказания (все позитивные)
    mock_outputs = MagicMock()
    mock_logits = torch.tensor([
        [0.3, 0.5, 2.0],  # Первый текст: позитивный (индекс 2)
        [0.2, 0.7, 1.8],  # Второй текст: позитивный
        [0.4, 0.4, 2.1]  # Третий текст: позитивный
    ])
    mock_outputs.logits = mock_logits

    mock_model.return_value = mock_outputs
    mock_model.eval = MagicMock()
    mock_model.to = MagicMock(return_value=mock_model)

    with patch('analyzer.AutoModelForSequenceClassification.from_pretrained',
               return_value=mock_model):
        with patch('analyzer.AutoTokenizer.from_pretrained'):
            sa = SentimentAnalyzer()

            texts = [
                "Отличная работа, рекомендую",
                "Качественное строительство, доволен",
                "Быстрая сдача объекта, спасибо"
            ]

            neg_share, total = sa.negative_share(texts)

            print(f"✅ Результаты для всех позитивных:")
            print(f"   Доля негативных: {neg_share:.2f} (ожидается 0.00)")
            print(f"   Всего текстов: {total}")

            assert neg_share == 0.0  # 0% негативных
            assert total == 3

    print("✅ Все позитивные тексты определены корректно")


def test_sentiment_mixed():
    """
    Тест анализатора со смешанными отзывами
    """
    print("\n Тест: test_sentiment_mixed")
    print("Проверяем анализ смешанных текстов (50/50)")

    # Мокаем модель для смешанных результатов
    mock_model = MagicMock()

    # Создаём моковые предсказания (50% негативных, 50% позитивных)
    mock_outputs = MagicMock()
    mock_logits = torch.tensor([
        [2.0, 0.5, 0.3],  # Негативный
        [0.3, 0.5, 2.0],  # Позитивный
        [1.8, 0.7, 0.2],  # Негативный
        [0.2, 0.7, 1.8],  # Позитивный
    ])
    mock_outputs.logits = mock_logits

    mock_model.return_value = mock_outputs
    mock_model.eval = MagicMock()
    mock_model.to = MagicMock(return_value=mock_model)

    with patch('analyzer.AutoModelForSequenceClassification.from_pretrained',
               return_value=mock_model):
        with patch('analyzer.AutoTokenizer.from_pretrained'):
            sa = SentimentAnalyzer()

            texts = [
                "Плохо", "Хорошо", "Ужасно", "Отлично"
            ]

            neg_share, total = sa.negative_share(texts)

            print(f"✅ Результаты для смешанных текстов:")
            print(f"   Доля негативных: {neg_share:.2f} (ожидается 0.50)")
            print(f"   Всего текстов: {total}")

            assert neg_share == 0.5  # 50% негативных
            assert total == 4

    print("✅ Смешанные тексты определены корректно")


def test_sentiment_batch_processing():
    """
    Тест обработки больших батчей
    """
    print("\n Тест: test_sentiment_batch_processing")
    print("Проверяем обработку большого количества текстов")

    sa = SentimentAnalyzer()

    # Создаём много тестовых текстов
    texts = ["Тестовый текст " + str(i) for i in range(35)]  # 35 текстов

    print(f" Создано {len(texts)} тестовых текстов")
    print(f"Batch size анализатора: {16} (по умолчанию)")

    neg_share, total = sa.negative_share(texts)

    print(f"✅ Обработано {total} текстов")
    print(f"   Доля негативных: {neg_share:.2f}")

    assert total == 35
    assert 0 <= neg_share <= 1

    print("✅ Большой батч обработан корректно")


def test_sentiment_model_loading():
    """
    Тест загрузки модели
    """
    print("\n Тест: test_sentiment_model_loading")
    print("Проверяем корректную загрузку модели BERT")

    sa = SentimentAnalyzer()

    # Проверяем, что модель загружена
    assert sa.model is not None
    assert sa.tokenizer is not None
    assert sa.device is not None

    print("✅ Модель загружена корректно:")
    print(f"   Модель: {type(sa.model).__name__}")
    print(f"   Токенизатор: {type(sa.tokenizer).__name__}")
    print(f"   Устройство: {sa.device}")

    # Проверяем метки классов
    assert sa.LABELS == {0: "negative", 1: "neutral", 2: "positive"}
    print("✅ Метки классов корректны")


def test_sentiment_predict_batch():
    """
    Тест метода predict_batch
    """
    print("\n Тест: test_sentiment_predict_batch")
    print("Проверяем метод predict_batch напрямую")

    sa = SentimentAnalyzer()

    texts = [
        "Очень плохо",
        "Нормально",
        "Очень хорошо"
    ]

    results = sa.predict_batch(texts, batch_size=2)

    print(f"✅ Получено {len(results)} результатов")

    # Проверяем структуру результатов
    for i, result in enumerate(results):
        assert "text" in result
        assert "label" in result
        assert result["label"] in ["negative", "neutral", "positive"]
        assert "negative_prob" in result
        assert "neutral_prob" in result
        assert "positive_prob" in result

        # Проверяем, что вероятности суммируются примерно в 1
        total_prob = result["negative_prob"] + result["neutral_prob"] + result["positive_prob"]
        assert 0.99 <= total_prob <= 1.01  # Допускаем небольшую погрешность

        print(f"   Текст {i + 1}: '{texts[i][:20]}...' → {result['label']}")

    print("✅ Метод predict_batch работает корректно")


def test_sentiment_edge_cases():
    """
    Тест граничных случаев
    """
    print("\n Тест: test_sentiment_edge_cases")
    print("Проверяем обработку граничных случаев")

    sa = SentimentAnalyzer()

    # Тест 1: очень длинный текст
    long_text = "Очень " * 100 + "длинный текст"
    neg_share, total = sa.negative_share([long_text])
    assert total == 1
    print(f"✅ Длинный текст обработан: {len(long_text)} символов")

    # Тест 2: текст с специальными символами
    special_text = "Текст с @#$% символами и emoji 😊"
    neg_share, total = sa.negative_share([special_text])
    assert total == 1
    print(f"✅ Текст со спецсимволами обработан")

    # Тест 3: пустая строка
    empty_text = ""
    neg_share, total = sa.negative_share([empty_text])
    assert total == 1
    print(f"✅ Пустая строка обработана")

    print("✅ Все граничные случаи обработаны корректно")


# Дополнительный тест для покрытия всех сценариев
def test_sentiment_integration():
    """
    Интеграционный тест анализатора тональности
    """
    print("\n Тест: test_sentiment_integration")
    print("Комплексный тест работы анализатора")

    sa = SentimentAnalyzer()

    # Реальные примеры отзывов о застройщиках
    reviews = [
        "Застройщик срывает сроки сдачи уже полгода, обещания не выполняет",
        "Качество строительства отличное, все по проекту",
        "Обманутые дольщики собирают подписи для обращения в прокуратуру",
        "Дом сдан вовремя, без замечаний, спасибо строителям",
        "Постоянные переносы сроков, коммуникации не подведены",
        "Цена/качество хорошее, инфраструктура развивается",
        "Брак в отделке, трещины в стенах, требуем исправления",
        "Рекомендую этого застройщика, ответственный подход",
        "Юридические проблемы у компании, суды с дольщиками",
        "Все устраивает, переехали, живем счастливо"
    ]

    print(f" Анализируем {len(reviews)} реалистичных отзывов о застройщиках")

    neg_share, total = sa.negative_share(reviews)

    print(f" Результаты анализа отзывов:")
    print(f"   Всего отзывов: {total}")
    print(f"   Доля негативных: {neg_share:.2f} ({neg_share * 100:.1f}%)")
    print(f"   Доля позитивных/нейтральных: {1 - neg_share:.2f} ({(1 - neg_share) * 100:.1f}%)")

    # Проверяем логические условия
    assert total == len(reviews)
    assert 0 <= neg_share <= 1

    # Анализируем распределение
    if neg_share > 0.5:
        print("Преобладают негативные отзывы (возможен рискованный застройщик)")
    elif neg_share < 0.3:
        print("✅ Преобладают позитивные отзывы (надёжный застройщик)")
    else:
        print(" Смешанные отзывы (требуется дополнительный анализ)")

    print(" Интеграционный тест завершен успешно!")


if __name__ == "__main__":
    """
    Запуск всех тестов анализатора тональности напрямую
    """
    print(" Запуск тестов анализатора тональности")
    print("=" * 60)

    # Список тестов для запуска
    tests = [
        test_sentiment_negative_share,
        test_sentiment_empty_list,
        test_sentiment_all_negative,
        test_sentiment_all_positive,
        test_sentiment_mixed,
        test_sentiment_batch_processing,
        test_sentiment_model_loading,
        test_sentiment_predict_batch,
        test_sentiment_edge_cases,
        test_sentiment_integration
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__}: PASSED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__}: FAILED - {e}\n")

    print("=" * 60)
    print(f" ИТОГ: {passed} пройдено, {failed} упало")

    if failed == 0:
        print(" Все тесты анализатора тональности прошли успешно!")
    else:
        print(" Некоторые тесты не прошли")
