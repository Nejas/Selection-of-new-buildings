from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from get_score import (
    get_buildings,
    get_known_developer_inns,
    get_rating_coverage,
    save_developer_rating,
)
from fastapi.middleware.cors import CORSMiddleware
from rating_client import (
    RatingServiceError,
    fetch_developer_dossier,
    fetch_developer_rating,
    refresh_developer_dossier,
)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ВНИМАНИЕ: разрешает запросы от всех источников
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все HTTP методы (GET, POST, PUT, DELETE, OPTIONS и т.д.)
    allow_headers=["*"],  # Разрешает все заголовки
)


class IndicatorsRequest(BaseModel):
    автовокзалы_и_автостанции: Optional[int] = Field(0, ge=0, le=10)
    больницы_взрослые: Optional[int] = Field(0, ge=0, le=10)
    входы_выходы_станций_метро: Optional[int] = Field(0, ge=0, le=10)
    городской_wi_fi: Optional[int] = Field(0, ge=0, le=10)
    карта_школьных_зон: Optional[int] = Field(0, ge=0, le=10)
    мфц: Optional[int] = Field(0, ge=0, le=10)
    нестационарные_торговые_объекты: Optional[int] = Field(0, ge=0, le=10)
    образовательные_учреждения: Optional[int] = Field(0, ge=0, le=10)
    образовательные_учреждения_город: Optional[int] = Field(0, ge=0, le=10)
    общественное_питание: Optional[int] = Field(0, ge=0, le=10)
    объекты_культурного_наследия: Optional[int] = Field(0, ge=0, le=10)
    организации_для_детей_сирот: Optional[int] = Field(0, ge=0, le=10)
    остановки_наземного_транспорта: Optional[int] = Field(0, ge=0, le=10)
    парковые_территории: Optional[int] = Field(0, ge=0, le=10)
    площадки_для_выгула_собак: Optional[int] = Field(0, ge=0, le=10)
    поликлиническая_помощь_взрослым: Optional[int] = Field(0, ge=0, le=10)
    скорая_и_неотложная_медицинская_п: Optional[int] = Field(0, ge=0, le=10)
    специализированные_медицинские_у: Optional[int] = Field(0, ge=0, le=10)
    станции_контроля_загрязнения_атмо: Optional[int] = Field(0, ge=0, le=10)
    станции_мцд: Optional[int] = Field(0, ge=0, le=10)
    стационарные_общественные_туалет: Optional[int] = Field(0, ge=0, le=10)
    стационарные_торговые_объекты: Optional[int] = Field(0, ge=0, le=10)
    точки_продажи_билетов: Optional[int] = Field(0, ge=0, le=10)
    центры_вакцинации: Optional[int] = Field(0, ge=0, le=10)
    центры_тестирования_для_выбора_сп: Optional[int] = Field(0, ge=0, le=10)
    reliability_mode: Literal["any", "known", "medium", "high"] = "any"

    @field_validator('*', mode='before')
    @classmethod
    def validate_values(cls, v):
        if not isinstance(v, (int, float)):
            return v
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Значение должно быть от 0 до 10')
        return v


@app.post("/find")
def save_indicators(request: IndicatorsRequest):
    payload = request.model_dump(exclude_none=True)
    reliability_mode = payload.pop("reliability_mode", "any")
    data = {key: value for key, value in payload.items() if value > 0}
    try:
        return get_buildings(data, reliability_mode=reliability_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ratings/coverage")
def ratings_coverage():
    try:
        return get_rating_coverage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ratings/developers/{inn}/refresh")
def refresh_developer_rating(inn: str):
    if not inn.isdigit() or len(inn) not in (10, 12):
        raise HTTPException(status_code=400, detail="Invalid INN format")

    try:
        rating = fetch_developer_rating(inn)
        score = rating.get("score")
        if score is None:
            return {
                "inn": inn,
                "updated_buildings": 0,
                "score": None,
                "status": rating.get("status", "Неизвестный"),
                "message": "Rating service returned no score",
            }

        updated = save_developer_rating(inn, score)
        return {
            "inn": inn,
            "updated_buildings": updated,
            "score": score,
            "status": rating.get("status"),
            "developer": rating.get("developer"),
        }
    except RatingServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ratings/developers/{inn}/dossier")
def developer_rating_dossier(inn: str):
    if not inn.isdigit() or len(inn) not in (10, 12):
        raise HTTPException(status_code=400, detail="Invalid INN format")

    try:
        return fetch_developer_dossier(inn)
    except RatingServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ratings/refresh-known")
def refresh_known_developer_ratings(limit: int = 20):
    limit = max(1, min(limit, 200))
    inns = get_known_developer_inns()[:limit]
    refreshed = []
    errors = []

    for inn in inns:
        try:
            rating = fetch_developer_rating(inn)
            score = rating.get("score")
            if score is None:
                refreshed.append(
                    {
                        "inn": inn,
                        "updated_buildings": 0,
                        "score": None,
                        "status": rating.get("status", "Неизвестный"),
                    }
                )
                continue

            updated = save_developer_rating(inn, score)
            refreshed.append(
                {
                    "inn": inn,
                    "updated_buildings": updated,
                    "score": score,
                    "status": rating.get("status"),
                }
            )
        except Exception as e:
            errors.append({"inn": inn, "error": str(e)})

    return {
        "requested": len(inns),
        "refreshed": refreshed,
        "errors": errors,
        "coverage": get_rating_coverage(),
    }


@app.post("/ratings/preload-known-dossiers")
def preload_known_developer_dossiers(limit: int = 20, force_refresh: bool = False):
    limit = max(1, min(limit, 200))
    inns = get_known_developer_inns()[:limit]
    refreshed = []
    errors = []

    for inn in inns:
        try:
            dossier = (
                refresh_developer_dossier(inn)
                if force_refresh
                else fetch_developer_dossier(inn)
            )
            score = dossier.get("score")
            updated = 0
            if score is not None:
                updated = save_developer_rating(inn, score)

            refreshed.append(
                {
                    "inn": inn,
                    "updated_buildings": updated,
                    "score": score,
                    "status": dossier.get("status"),
                    "cached": dossier.get("cached", False),
                }
            )
        except Exception as e:
            errors.append({"inn": inn, "error": str(e)})

    return {
        "requested": len(inns),
        "refreshed": refreshed,
        "errors": errors,
        "coverage": get_rating_coverage(),
    }
