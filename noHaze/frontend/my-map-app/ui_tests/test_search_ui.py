"""Browser checks for the main search journeys, with a local fake API."""
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FRONTEND_URL = os.environ.get("UI_TEST_URL", "http://localhost:3000")
BUILDING = {
    "id": 1, "address": "Тестовая улица, 1", "developer_name": "Тестовый застройщик",
    "developer_inn": "7700000000", "developer_reliability_score": 85,
    "latitude": 55.751244, "longitude": 37.618423,
}
DOSSIER = {
    "status": "Высокая надёжность", "score": 85,
    "updated_at": "2026-01-01T12:00:00Z", "details": {}, "factors": {},
    "projects": [], "legal_events": [], "news": [],
}


class FakeAPI(BaseHTTPRequestHandler):
    fail_search = False
    empty_search = False
    fail_dossier = False
    last_search = None

    def log_message(self, *args):
        pass

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(200, {})

    def do_POST(self):
        if self.path != "/find":
            return self.send_json(404, {})
        FakeAPI.last_search = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_json(503 if FakeAPI.fail_search else 200, {} if FakeAPI.fail_search or FakeAPI.empty_search else {"0": BUILDING})

    def do_GET(self):
        if self.path == "/ratings/developers/7700000000/dossier":
            return self.send_json(503, {}) if FakeAPI.fail_dossier else self.send_json(200, DOSSIER)
        self.send_json(404, {})


class SearchUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.server = ThreadingHTTPServer(("127.0.0.1", 8000), FakeAPI)
        except OSError as exc:
            raise RuntimeError("Порт 8000 занят: остановите API перед запуском UI-тестов") from exc
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,900")
        try:
            cls.driver = webdriver.Chrome(options=options)
        except Exception:
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join()
            raise
        cls.wait = WebDriverWait(cls.driver, 15)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        FakeAPI.fail_search = False
        FakeAPI.empty_search = False
        FakeAPI.fail_dossier = False
        FakeAPI.last_search = None
        self.driver.set_window_size(1440, 900)
        self.driver.get(FRONTEND_URL)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".floating-widget")))

    def click(self, selector):
        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element.click()
        return element

    def choose_high_and_metro(self):
        self.driver.find_element(By.XPATH, "//button[normalize-space()='Высокая']").click()
        self.click('[title="Развернуть все"]')
        slider = self.driver.find_element(By.XPATH, "//div[contains(@class,'widget-parameter')][.//label[normalize-space()='Входы/выходы станций метро']]//input")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", slider)
        slider.send_keys(Keys.HOME, Keys.ARROW_RIGHT, Keys.ARROW_RIGHT, Keys.ARROW_RIGHT)
        self.assertEqual(slider.get_attribute("value"), "3")
        return slider

    def search(self):
        self.click(".widget-search-btn")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".result-card")))

    def test_search_and_open_dossier(self):
        self.choose_high_and_metro()
        self.search()
        self.assertEqual(FakeAPI.last_search["reliability_mode"], "high")
        self.assertEqual(FakeAPI.last_search["входы_выходы_станций_метро"], 3)
        self.assertIn("Тестовая улица, 1", self.driver.find_element(By.CSS_SELECTOR, ".result-card").text)
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".leaflet-marker-icon").is_displayed())
        self.click(".result-card")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".details-content")))
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".details-content"), "Тестовый застройщик"))
        self.click(".dossier-toggle")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".rating-dossier")))
        self.assertIn("Дата расчёта", self.driver.find_element(By.CSS_SELECTOR, ".rating-dossier").text)

    def test_reset_restores_values_and_results(self):
        slider = self.choose_high_and_metro()
        self.search()
        self.click('[title="Сбросить значения"]')
        self.assertEqual(slider.get_attribute("value"), "0")
        self.assertIn("active", self.driver.find_element(By.XPATH, "//button[normalize-space()='Не учитывать']").get_attribute("class"))
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".result-card"))

    def test_api_error_is_visible(self):
        FakeAPI.fail_search = True
        self.click(".widget-search-btn")
        message = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".widget-error")))
        self.assertIn("Ошибка при получении данных", message.text)
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".widget-search-btn").is_enabled())

    def test_controls_at_desktop_and_mobile_width(self):
        for width, height in ((1440, 900), (390, 844)):
            with self.subTest(width=width):
                self.driver.set_window_size(width, height)
                self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".floating-widget").is_displayed())
                button = self.driver.find_element(By.CSS_SELECTOR, ".widget-search-btn")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                self.assertTrue(button.is_displayed() and button.is_enabled())
                self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".leaflet-container").is_displayed())


    def test_hide_and_show_filters(self):
        self.click('[title="Скрыть фильтры"]')
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".floating-widget"))
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".leaflet-container").is_displayed())
        self.click('[title="Показать фильтры"]')
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".floating-widget")))

    def test_collapse_and_expand_categories(self):
        self.click('[title="Свернуть все"]')
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".widget-category-parameters"))
        self.click('[title="Развернуть все"]')
        categories = self.driver.find_elements(By.CSS_SELECTOR, ".widget-category")
        self.assertGreater(len(categories), 0)
        self.assertEqual(len(self.driver.find_elements(By.CSS_SELECTOR, ".widget-category-parameters")), len(categories))

    def test_empty_search_results(self):
        FakeAPI.empty_search = True
        self.click(".widget-search-btn")
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".widget-results-info"), "Найдено: 0"))
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".result-card"))
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".leaflet-container").is_displayed())

    def test_close_and_reopen_building_card(self):
        self.search()
        self.click(".result-card")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".details-content")))
        self.click(".details-content .close-btn")
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".details-panel")))
        self.click(".result-card")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".details-content")))
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".details-content"), "Тестовая улица, 1"))

    def test_dossier_error_is_visible(self):
        FakeAPI.fail_dossier = True
        self.search()
        self.click(".result-card")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".details-content")))
        self.click(".dossier-toggle")
        message = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".rating-dossier-state.error")))
        self.assertIn("Не удалось загрузить подробности оценки", message.text)

    def test_search_succeeds_after_api_error(self):
        FakeAPI.fail_search = True
        self.click(".widget-search-btn")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".widget-error")))
        FakeAPI.fail_search = False
        self.search()
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".widget-error"))
        self.assertIn("Тестовая улица, 1", self.driver.find_element(By.CSS_SELECTOR, ".result-card").text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
