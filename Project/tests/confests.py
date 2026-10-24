# """
# Конфигурация pytest для отображения вывода
# """

# import sys
# from pathlib import Path

# # Добавляем корневую директорию в путь Python
# ROOT = Path(__file__).resolve().parents[1]
# sys.path.insert(0, str(ROOT))

# def pytest_configure(config):
#     """Настройка pytest"""
#     print("\n" + "="*80)
#     print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ")
#     print("="*80 + "\n")

# def pytest_sessionfinish(session, exitstatus):
#     """Завершение сессии тестирования"""
#     print("\n" + "="*80)
#     if exitstatus == 0:
#         print("✅ ТЕСТИРОВАНИЕ УСПЕШНО ЗАВЕРШЕНО")
#     else:
#         print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
#     print("="*80)

# # Опционально: кастомный хук для вывода результатов
# def pytest_runtest_logreport(report):
#     """Вывод результатов каждого теста"""
#     if report.when == "call":  # Только при вызове теста
#         if report.passed:
#             print(f"✅ {report.nodeid}: PASSED")
#         elif report.failed:
#             print(f"❌ {report.nodeid}: FAILED")
#         elif report.skipped:
#             print(f"⏭️  {report.nodeid}: SKIPPED")