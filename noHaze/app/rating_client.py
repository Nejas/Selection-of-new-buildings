import os

import requests


RATING_SERVICE_URL = os.getenv("RATING_SERVICE_URL", "http://localhost:8001")
RATING_SERVICE_TIMEOUT = float(os.getenv("RATING_SERVICE_TIMEOUT", "60"))


class RatingServiceError(RuntimeError):
    pass


def fetch_developer_rating(inn: str) -> dict:
    response = requests.get(
        f"{RATING_SERVICE_URL.rstrip('/')}/api/score/{inn}",
        timeout=RATING_SERVICE_TIMEOUT,
    )

    if response.status_code >= 400:
        raise RatingServiceError(
            f"Rating service returned {response.status_code}: {response.text}"
        )

    data = response.json()
    if "score" not in data:
        raise RatingServiceError("Rating service response does not contain score")

    return data


def fetch_developer_dossier(inn: str) -> dict:
    response = requests.get(
        f"{RATING_SERVICE_URL.rstrip('/')}/api/developers/{inn}/dossier",
        timeout=RATING_SERVICE_TIMEOUT,
    )

    if response.status_code >= 400:
        raise RatingServiceError(
            f"Rating service returned {response.status_code}: {response.text}"
        )

    return response.json()


def refresh_developer_dossier(inn: str) -> dict:
    response = requests.get(
        f"{RATING_SERVICE_URL.rstrip('/')}/api/developers/{inn}/dossier",
        params={"refresh": "true"},
        timeout=RATING_SERVICE_TIMEOUT,
    )

    if response.status_code >= 400:
        raise RatingServiceError(
            f"Rating service returned {response.status_code}: {response.text}"
        )

    return response.json()
