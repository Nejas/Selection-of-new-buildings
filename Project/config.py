import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:Huma2005@localhost:5432/Developer_rating",
    )
    eisjs_api_url: str = os.getenv("EISJS_API_URL", "https://apidata.mos.ru/v1/datasets")
    eisjs_api_key: str | None = os.getenv("EISJS_API_KEY")
    developers_data_path: str = os.getenv(
        "DEVELOPERS_DATA_PATH",
        "Data/domrfdevelopers_final.json",
    )
    projects_data_path: str = os.getenv(
        "PROJECTS_DATA_PATH",
        "Data/domrfkn_current.jsonl",
    )
    problem_objects_report_path: str = os.getenv(
        "PROBLEM_OBJECTS_REPORT_PATH",
        "Data/problem_objects_02_05_2026.xlsx",
    )
    projects_snapshot_date: str = os.getenv("PROJECTS_SNAPSHOT_DATE", "2021-10-08")
    news_rss_url_template: str = os.getenv(
        "NEWS_RSS_URL_TEMPLATE",
        "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru",
    )
    news_limit: int = int(os.getenv("NEWS_LIMIT", "30"))
    checko_api_url: str = os.getenv("CHECKO_API_URL", "https://api.checko.ru/v2/legal-cases")
    checko_api_key: str | None = os.getenv("CHECKO_API_KEY")
    checko_legal_cases_limit: int = int(os.getenv("CHECKO_LEGAL_CASES_LIMIT", "100"))
    dadata_api_key: str | None = os.getenv("DADATA_API_KEY")
    dadata_secret_key: str | None = os.getenv("DADATA_SECRET_KEY")


settings = Settings()
