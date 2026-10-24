from datetime import datetime

import httpx

from config import settings
from models import LegalEvent


class CheckoLegalEventsParser:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        limit: int | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.checko_api_key
        self.api_url = api_url or settings.checko_api_url
        self.limit = limit or settings.checko_legal_cases_limit
        self.client = client or httpx.AsyncClient(timeout=20)

    async def parse(self, inn: str) -> list[LegalEvent]:
        if not self.api_key:
            print("[LegalEvents] CHECKO_API_KEY не задан, правовой источник пропущен")
            return []

        print(f"[LegalEvents] Загрузка арбитражных дел Checko: ИНН={inn}")

        try:
            response = await self.client.get(
                self.api_url,
                params={
                    "key": self.api_key,
                    "inn": inn,
                    "actual": "true",
                    "limit": self.limit,
                    "sort": "-date",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            print(f"[LegalEvents] Ошибка Checko API: {exc}")
            return []

        meta = payload.get("meta") or {}
        if meta.get("status") == "error":
            print(f"[LegalEvents] Checko API вернул ошибку: {meta.get('message')}")
            return []

        records = (payload.get("data") or {}).get("Записи") or []
        events = [
            self._to_event(record, inn)
            for record in records
            if self._is_negative_record(record, inn)
        ]
        print(
            "[LegalEvents] Найдено негативных правовых событий: "
            f"{len(events)} из {len(records)} полученных"
        )
        return events

    def _to_event(self, record: dict, inn: str) -> LegalEvent:
        role = self._role(record, inn)
        case_number = record.get("Номер", "")
        court = record.get("Суд", "")
        claim_amount = record.get("СуммИск")

        return LegalEvent(
            date=self._parse_date(record.get("Дата")),
            event_type=f"court_case_{role}",
            status="actual",
            source=record.get("СтрКАД", "checko.ru"),
            description=self._description(case_number, court, claim_amount),
        )

    def _role(self, record: dict, inn: str) -> str:
        if self._party_contains_inn(record.get("Ответ") or [], inn):
            return "defendant"
        if self._party_contains_inn(record.get("Ист") or [], inn):
            return "plaintiff"
        return "participant"

    def _is_negative_record(self, record: dict, inn: str) -> bool:
        return self._role(record, inn) == "defendant"

    def _party_contains_inn(self, parties: list[dict], inn: str) -> bool:
        return any(str(party.get("ИНН") or "").strip() == inn for party in parties)

    def _description(self, case_number: str, court: str, claim_amount) -> str:
        parts = []
        if case_number:
            parts.append(f"Дело {case_number}")
        if court:
            parts.append(court)
        if claim_amount:
            parts.append(f"Сумма иска: {claim_amount}")
        return "; ".join(parts)

    def _parse_date(self, value: str | None) -> datetime:
        if not value:
            return datetime.now()
        return datetime.fromisoformat(value)
