import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import settings
from models import Project


@dataclass(frozen=True)
class DeveloperProfile:
    inn: str
    name: str
    registration_date: datetime | None = None
    region: str | None = None
    problem_objects_count: int = 0
    building_objects_count: int = 0
    commissioned_objects_count: int = 0


class LocalDevelopersRepository:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or settings.developers_data_path)
        self._by_inn: dict[str, DeveloperProfile] | None = None

    def find_by_inn(self, inn: str) -> DeveloperProfile | None:
        if self._by_inn is None:
            self._by_inn = self._load_index()
        return self._by_inn.get(inn)

    def search(self, query: str, limit: int = 20) -> list[DeveloperProfile]:
        if self._by_inn is None:
            self._by_inn = self._load_index()

        normalized_query = self._normalize(query)
        if not normalized_query:
            return []

        matches = []
        for profile in self._by_inn.values():
            if (
                normalized_query in self._normalize(profile.name)
                or normalized_query in profile.inn
            ):
                matches.append(profile)

        return sorted(matches, key=lambda profile: profile.name)[:limit]

    def all(self) -> list[DeveloperProfile]:
        if self._by_inn is None:
            self._by_inn = self._load_index()
        return list(self._by_inn.values())

    def statistics(self, limit: int = 10) -> dict:
        developers = self.all()
        regions = Counter(profile.region or "Не указан" for profile in developers)
        top_builders = sorted(
            developers,
            key=lambda profile: profile.building_objects_count,
            reverse=True,
        )[:limit]
        top_problem = sorted(
            developers,
            key=lambda profile: profile.problem_objects_count,
            reverse=True,
        )[:limit]

        return {
            "developers_count": len(developers),
            "regions_count": len(regions),
            "top_regions": [
                {"region": region, "developers_count": count}
                for region, count in regions.most_common(limit)
            ],
            "top_building_developers": [
                {
                    "inn": profile.inn,
                    "name": profile.name,
                    "building_objects_count": profile.building_objects_count,
                    "region": profile.region,
                }
                for profile in top_builders
            ],
            "top_problem_developers": [
                {
                    "inn": profile.inn,
                    "name": profile.name,
                    "problem_objects_count": profile.problem_objects_count,
                    "region": profile.region,
                }
                for profile in top_problem
                if profile.problem_objects_count > 0
            ],
        }

    def _load_index(self) -> dict[str, DeveloperProfile]:
        if not self.path.exists():
            print(f"[DevelopersRepository] Файл не найден: {self.path}")
            return {}

        developers = {}
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                inn = str(row.get("devInn") or "").strip()
                if not inn:
                    continue
                developers[inn] = self._to_profile(row)

        print(f"[DevelopersRepository] Загружено застройщиков: {len(developers)}")
        return developers

    def _to_profile(self, row: dict) -> DeveloperProfile:
        inn = str(row.get("devInn") or "").strip()
        name = (
            row.get("devShortCleanNm")
            or row.get("devShortNm")
            or row.get("devFullCleanNm")
            or f"Застройщик {inn}"
        )

        return DeveloperProfile(
            inn=inn,
            name=name,
            registration_date=self._registration_date_from_ogrn(row.get("devOgrn")),
            region=row.get("regRegionDesc"),
            problem_objects_count=int(row.get("problObjCnt", 0) or 0),
            building_objects_count=int(row.get("buildObjCnt", 0) or 0),
            commissioned_objects_count=int(row.get("comissObjCnt", 0) or 0),
        )

    def _registration_date_from_ogrn(self, ogrn: str | None) -> datetime | None:
        if not ogrn:
            return None

        ogrn = str(ogrn).strip()
        if len(ogrn) < 3 or not ogrn[:3].isdigit():
            return None

        year_suffix = int(ogrn[1:3])
        current_suffix = datetime.now().year % 100
        year = 2000 + year_suffix if year_suffix <= current_suffix else 1900 + year_suffix
        return datetime(year, 1, 1)

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().replace("ё", "е").split())


class LocalProjectsRepository:
    def __init__(self, path: str | Path | None = None, snapshot_date: str | datetime | None = None):
        self.path = Path(path or settings.projects_data_path)
        self.snapshot_date = self._parse_snapshot_date(snapshot_date or settings.projects_snapshot_date)
        self._by_inn: dict[str, list[Project]] | None = None

    def find_by_developer_inn(self, inn: str) -> list[Project]:
        if self._by_inn is None:
            self._by_inn = self._load_index()
        return list(self._by_inn.get(inn, []))

    def statistics(self) -> dict:
        if self._by_inn is None:
            self._by_inn = self._load_index()

        projects = [project for items in self._by_inn.values() for project in items]
        delayed = [project for project in projects if project.delay_count > 0]
        problem = [project for project in projects if project.is_problem]
        total_area = sum(project.area for project in projects)

        return {
            "projects_count": len(projects),
            "developers_with_projects_count": len(self._by_inn),
            "delayed_projects_count": len(delayed),
            "problem_projects_count": len(problem),
            "living_area_total": round(total_area, 2),
            "avg_delay_days": (
                round(sum(project.delay_days_avg for project in projects) / len(projects), 2)
                if projects
                else 0
            ),
        }

    def _load_index(self) -> dict[str, list[Project]]:
        if not self.path.exists():
            print(f"[ProjectsRepository] Файл не найден: {self.path}")
            return {}

        projects_by_inn: dict[str, list[Project]] = {}
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                developer = row.get("developer") or {}
                inn = str(developer.get("devInn") or "").strip()
                if not inn:
                    continue
                projects_by_inn.setdefault(inn, []).append(self._to_project(row))

        total = sum(len(projects) for projects in projects_by_inn.values())
        print(f"[ProjectsRepository] Загружено объектов: {total}")
        return projects_by_inn

    def _to_project(self, row: dict) -> Project:
        ready_date = self._parse_date(row.get("objReady100PercDt"))
        delay_days = self._delay_days(row, ready_date)

        return Project(
            name=row.get("objCommercNm") or row.get("objAddr") or f"Объект {row.get('objId', '')}",
            planned_date=ready_date,
            current_planned_date=self.snapshot_date if delay_days > 0 else ready_date,
            delay_days_avg=delay_days,
            delay_count=1 if delay_days > 0 else 0,
            is_problem=self._is_problem(row),
            area=float(row.get("objSquareLiving", 0) or 0),
        )

    def _parse_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    def _parse_snapshot_date(self, value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)

    def _delay_days(self, row: dict, ready_date: datetime | None) -> int:
        if not ready_date:
            return 0

        site_status = str(row.get("siteStatus") or "").lower()
        is_building = "стро" in site_status or row.get("objStatus") == 0
        if not is_building:
            return 0

        return max((self.snapshot_date.date() - ready_date.date()).days, 0)

    def _is_problem(self, row: dict) -> bool:
        return bool(row.get("objProblemFlg")) or row.get("problemFlag") not in (None, "", "NONE")
