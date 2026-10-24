import asyncio
from datetime import datetime
from aggregator import Aggregator
from scoring import ScoringService


async def main():
    """
    Основная асинхронная функция для загрузки и оценки застройщика
    """
    agg = Aggregator()
    service = ScoringService()

    print("=" * 50)
    print("СИСТЕМА ОЦЕНКИ ЗАСТРОЙЩИКОВ")
    print("=" * 50)

    try:
        # ВАЖНО: используем await для асинхронного метода load()
        dev = await agg.load(
            inn="1234567890"
        )

        print(f"[OK] Загружен застройщик: {dev.name}")
        print(f"   ИНН: {dev.inn}")
        print(f"   Проектов: {len(dev.projects)}")
        print(f"   Дата регистрации: {dev.registration_date}")

        # Выполняем оценку
        print("\nВыполнение оценки...")
        result = service.evaluate(dev)

        print("\nРЕЗУЛЬТАТЫ ОЦЕНКИ:")
        print("-" * 30)
        print(f"Застройщик: {result['developer']}")
        print(f"Оценка: {result['score']}")
        print(f"Статус: {result['status']}")
        print("-" * 30)

        return result

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


# Запускаем асинхронную функцию
if __name__ == "__main__":
    asyncio.run(main())
