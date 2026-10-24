import subprocess
import sys
from datetime import datetime


def run_tests():
    """Запускает все тесты с красивым выводом"""

    print("=" * 70)
    print("🚀 ЗАПУСК ТЕСТОВ СИСТЕМЫ ОЦЕНКИ ЗАСТРОЙЩИКОВ")
    print("=" * 70)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Команда для запуска pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Подробный вывод
        "--tb=short",  # Короткий traceback
        "--color=yes",  # Цветной вывод
        "-q"  # Тихий режим в конце
    ]

    try:
        # Запускаем тесты
        print("🔍 Запускаем тесты...")
        print("-" * 70)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        # Выводим результаты
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("-" * 70)

        # Разделяем вывод на части
        lines = result.stdout.split('\n')

        for line in lines:
            if line.strip():  # Пропускаем пустые строки
                print(line)

        # Выводим статистику
        print("\n" + "=" * 70)
        print("📈 СВОДКА:")

        # Анализируем вывод
        passed = 0
        failed = 0

        for line in lines:
            if "PASSED" in line:
                passed += 1
            elif "FAILED" in line:
                failed += 1

        total = passed + failed

        print(f"   Всего тестов: {total}")
        print(f"   ✅ Успешно:   {passed}")
        print(f"    Провалено: {failed}")
        print(f"    Успешность: {passed / total * 100:.1f}%" if total > 0 else "   📊 Успешность: N/A")

        if failed == 0:
            print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            return 0
        else:
            print(f"\n❌ НЕ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            return 1

    except Exception as e:
        print(f"\n Ошибка при запуске тестов: {e}")
        return 1


if __name__ == "__main__":
    print(" Python тестовая система v1.0\n")
    exit_code = run_tests()
    sys.exit(exit_code)