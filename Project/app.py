from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, date
from pathlib import Path
from pydantic import BaseModel
from db import AsyncSessionLocal, engine
from models_db import Base, DeveloperDB, DeveloperDossierDB, NewsSourceDB, RatingDB
from sqlalchemy import select
from aggregator import Aggregator
from news_sources import seed_default_news_sources
from problem_objects_report import ProblemObjectsReportRepository
from scoring import ScoringService


class NewsSourceCreate(BaseModel):
    name: str
    url_template: str
    source_type: str = "rss"
    requires_query: bool = False
    is_active: bool = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_default_news_sources(session)
    print("[APP] База данных инициализирована")
    yield
    print(" [APP] Завершение работы")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
agg = Aggregator()
scoring = ScoringService()
problem_objects_report = ProblemObjectsReportRepository()


async def get_or_create_developer(session, dev):
    stmt = select(DeveloperDB).where(DeveloperDB.inn == dev.inn)
    res = await session.execute(stmt)
    db_dev = res.scalar_one_or_none()

    if db_dev:
        db_dev.name = dev.name
        db_dev.registration_date = dev.registration_date.date()
        return db_dev

    db_dev = DeveloperDB(
        inn=dev.inn,
        name=dev.name,
        registration_date=dev.registration_date.date(),
    )
    session.add(db_dev)
    await session.flush()
    return db_dev


def build_dossier_payload(dev, result):
    return {
        **result,
        "projects": [
            {
                "name": project.name,
                "planned_date": project.planned_date.date().isoformat() if project.planned_date else None,
                "current_planned_date": (
                    project.current_planned_date.date().isoformat()
                    if project.current_planned_date
                    else None
                ),
                "delay_days_avg": project.delay_days_avg,
                "delay_count": project.delay_count,
                "is_problem": project.is_problem,
                "area": project.area,
            }
            for project in dev.projects
        ],
        "legal_events": [
            {
                "date": event.date.date().isoformat(),
                "event_type": event.event_type,
                "status": event.status,
                "source": event.source,
                "description": event.description,
            }
            for event in dev.legal_events
        ],
        "news": [
            {
                "title": news.title,
                "summary": news.summary,
                "published_at": news.published_at.date().isoformat() if news.published_at else None,
                "link": news.link,
                "sentiment": news.sentiment,
            }
            for news in dev.news_mentions
        ],
    }


async def save_rating_and_dossier(dev, payload):
    async with AsyncSessionLocal() as session:
        db_dev = await get_or_create_developer(session, dev)

        if payload.get("score") not in (None, 0):
            session.add(
                RatingDB(
                    developer_id=db_dev.id,
                    score=payload["score"],
                    status=payload["status"],
                    rating_date=date.today(),
                )
            )

        stmt = select(DeveloperDossierDB).where(DeveloperDossierDB.developer_id == db_dev.id)
        res = await session.execute(stmt)
        dossier = res.scalar_one_or_none()

        if not dossier:
            dossier = DeveloperDossierDB(developer_id=db_dev.id)
            session.add(dossier)

        dossier.score = payload.get("score")
        dossier.status = payload.get("status", "Неизвестный")
        dossier.details = payload.get("details", {})
        dossier.factors = payload.get("factors", {})
        dossier.projects = payload.get("projects", [])
        dossier.legal_events = payload.get("legal_events", [])
        dossier.news = payload.get("news", [])
        dossier.updated_at = datetime.utcnow()

        await session.commit()


def cached_dossier_payload(db_dev, dossier):
    return {
        "developer": db_dev.name,
        "score": dossier.score,
        "status": dossier.status,
        "details": dossier.details,
        "factors": dossier.factors,
        "projects": dossier.projects,
        "legal_events": dossier.legal_events,
        "news": dossier.news,
        "cached": True,
        "updated_at": dossier.updated_at.isoformat() if dossier.updated_at else None,
    }


@app.get("/api/score/{inn}")
async def score_developer(inn: str):
    print(f"\n [API] Запрос оценки: ИНН={inn}")

    if not inn.isdigit() or len(inn) not in (10, 12):
        print("[API] Невалидный ИНН")
        raise HTTPException(status_code=400, detail="Invalid INN format")

    try:
        dev = await agg.load(inn=inn)
        result = scoring.evaluate(dev)

        if result.get("score") is None:
            print(" [API] Score=None -> Неизвестный")
            result["status"] = "Неизвестный"

    except Exception as e:
        print(f" [API] Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    payload = build_dossier_payload(dev, result)
    await save_rating_and_dossier(dev, payload)

    print("[API] Ответ отправлен клиенту")
    return result


@app.get("/api/developers/{inn}/dossier")
async def developer_dossier(inn: str, refresh: bool = False):
    if not inn.isdigit() or len(inn) not in (10, 12):
        raise HTTPException(status_code=400, detail="Invalid INN format")

    if not refresh:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(DeveloperDB, DeveloperDossierDB)
                .join(DeveloperDossierDB, DeveloperDossierDB.developer_id == DeveloperDB.id)
                .where(DeveloperDB.inn == inn)
            )
            res = await session.execute(stmt)
            row = res.first()
            if row:
                return cached_dossier_payload(row[0], row[1])

    dev = await agg.load(inn=inn)
    result = scoring.evaluate(dev)
    payload = build_dossier_payload(dev, result)
    await save_rating_and_dossier(dev, payload)

    return {**payload, "cached": False}


@app.get("/api/developers/search")
async def search_developers(query: str, limit: int = 20):
    if len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must contain at least 2 characters")

    limit = max(1, min(limit, 100))
    matches = agg.developers.search(query, limit=limit)

    return [
        {
            "inn": developer.inn,
            "name": developer.name,
            "registration_date": (
                developer.registration_date.date().isoformat()
                if developer.registration_date
                else None
            ),
            "region": developer.region,
            "problem_objects_count": developer.problem_objects_count,
            "building_objects_count": developer.building_objects_count,
            "commissioned_objects_count": developer.commissioned_objects_count,
        }
        for developer in matches
    ]


@app.get("/api/statistics/overview")
async def statistics_overview():
    developer_stats = agg.developers.statistics()
    project_stats = agg.projects.statistics()
    problem_report = problem_objects_report.load()

    return {
        "developers": developer_stats,
        "projects": project_stats,
        "problem_objects_report": (
            {
                "report_date": problem_report.report_date,
                "houses_count": problem_report.houses_count,
                "developers_count": problem_report.developers_count,
                "living_area_thousand_m2": problem_report.living_area_thousand_m2,
            }
            if problem_report
            else None
        ),
    }

@app.get("/")
async def root():
    return FileResponse(Path("static") / "index.html")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/problem-objects/summary")
async def problem_objects_summary():
    report = problem_objects_report.load()
    if report is None:
        raise HTTPException(status_code=404, detail="Problem objects report not found")

    return {
        "report_date": report.report_date,
        "houses_count": report.houses_count,
        "developers_count": report.developers_count,
        "living_area_thousand_m2": report.living_area_thousand_m2,
        "regions": [
            {
                "region": region.region,
                "houses_count": region.houses_count,
                "developers_count": region.developers_count,
                "living_area_thousand_m2": region.living_area_thousand_m2,
            }
            for region in report.regions
        ],
    }


@app.get("/api/news-sources")
async def list_news_sources():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(NewsSourceDB).order_by(NewsSourceDB.id))
        sources = result.scalars().all()

    return [
        {
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "url_template": source.url_template,
            "requires_query": source.requires_query,
            "is_active": source.is_active,
        }
        for source in sources
    ]


@app.post("/api/news-sources")
async def create_news_source(source: NewsSourceCreate):
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(NewsSourceDB).where(NewsSourceDB.name == source.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="News source already exists")

        db_source = NewsSourceDB(**source.model_dump())
        session.add(db_source)
        await session.commit()
        await session.refresh(db_source)

    return {
        "id": db_source.id,
        "name": db_source.name,
        "source_type": db_source.source_type,
        "url_template": db_source.url_template,
        "requires_query": db_source.requires_query,
        "is_active": db_source.is_active,
    }


@app.patch("/api/news-sources/{source_id}/toggle")
async def toggle_news_source(source_id: int):
    async with AsyncSessionLocal() as session:
        source = await session.get(NewsSourceDB, source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="News source not found")

        source.is_active = not source.is_active
        await session.commit()
        await session.refresh(source)

    return {
        "id": source.id,
        "name": source.name,
        "is_active": source.is_active,
    }

