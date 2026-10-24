import httpx
from datetime import datetime
from models import Project
from config import settings


class AsyncEISJSParser:
    def __init__(self, api_key: str | None = None, url: str | None = None):
        self.url = url or settings.eisjs_api_url
        self.client = httpx.AsyncClient(timeout=10)
        self.api_key = api_key if api_key is not None else settings.eisjs_api_key

    async def _make_request(self, inn: str) -> dict:
        params = {"inn": inn}
        if self.api_key:
            params["api_key"] = self.api_key

        resp = await self.client.get(
            self.url,
            params=params
        )
        resp.raise_for_status()
        return resp.json()

    async def parse(self, inn: str):
        print(f"\n [EISJS] Парсинг объектов по ИНН {inn}")

        try:
            data = await self._make_request(inn)
        except Exception as e:
            print(f"Ошибка: {e}")
            return []

        objects = self._extract_objects(data)
        if objects is None:
            print("Некорректная структура")
            return []

        projects = []

        for o in objects:
            try:
                project = self._to_project(o)
                projects.append(project)
            except Exception as e:
                print(f"Ошибка обработки: {e}")

        print(f"[EISJS] Загружено: {len(projects)}")
        return projects

    def _extract_objects(self, data: dict) -> list[dict] | None:
        if not isinstance(data, dict):
            return None

        if isinstance(data.get("objects"), list):
            return data["objects"]

        if isinstance(data.get("Items"), list):
            return data["Items"]

        return None

    def _to_project(self, obj: dict) -> Project:
        return Project(
            name=obj.get("name") or obj.get("Caption", ""),
            planned_date=self._parse_date(obj.get("plan_initial") or obj.get("PublishDate")),
            current_planned_date=self._parse_date(obj.get("plan_current") or obj.get("LastUpdateDate")),
            delay_days_avg=float(obj.get("delay_days_avg", 0) or 0),
            delay_count=int(obj.get("delay_count", 0) or 0),
            is_problem=bool(obj.get("is_problem", obj.get("IsArchive", False))),
            area=float(obj.get("area", 0) or 0),
        )

    def _parse_date(self, value: str | None):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
