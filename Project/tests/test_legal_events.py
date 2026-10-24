import pytest

from legal_events import CheckoLegalEventsParser


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class MockClient:
    async def get(self, url, params):
        return MockResponse(
            {
                "meta": {"status": "ok"},
                "data": {
                    "Записи": [
                        {
                            "Номер": "А40-1/2024",
                            "Дата": "2024-01-10",
                            "Суд": "Арбитражный суд города Москвы",
                            "СтрКАД": "https://kad.arbitr.ru/Card/1",
                            "Ист": [{"ИНН": "1111111111", "Наим": "Истец"}],
                            "Ответ": [{"ИНН": params["inn"], "Наим": "Ответчик"}],
                            "СуммИск": 1500000,
                        },
                        {
                            "Номер": "А40-2/2024",
                            "Дата": "2024-02-10",
                            "Суд": "Арбитражный суд города Москвы",
                            "СтрКАД": "https://kad.arbitr.ru/Card/2",
                            "Ист": [{"ИНН": params["inn"], "Наим": "Истец"}],
                            "Ответ": [{"ИНН": "2222222222", "Наим": "Ответчик"}],
                            "СуммИск": 700000,
                        }
                    ]
                },
            }
        )


@pytest.mark.asyncio
async def test_checko_legal_events_parser_maps_cases_to_events():
    parser = CheckoLegalEventsParser(api_key="test", client=MockClient())

    events = await parser.parse("7701651356")

    assert len(events) == 1
    assert events[0].event_type == "court_case_defendant"
    assert events[0].date.year == 2024
    assert events[0].source == "https://kad.arbitr.ru/Card/1"
    assert "А40-1/2024" in events[0].description


@pytest.mark.asyncio
async def test_checko_legal_events_parser_uses_only_defendant_cases():
    parser = CheckoLegalEventsParser(api_key="test", client=MockClient())

    events = await parser.parse("7701651356")

    assert len(events) == 1
    assert events[0].event_type == "court_case_defendant"
    assert "А40-2/2024" not in events[0].description


@pytest.mark.asyncio
async def test_checko_legal_events_parser_skips_without_api_key():
    parser = CheckoLegalEventsParser(api_key="", client=MockClient())

    events = await parser.parse("7701651356")

    assert events == []
