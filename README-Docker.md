# Docker запуск

Проект раскладывается на четыре контейнера:

- `db` - PostgreSQL/PostGIS с базами `practicum` и `Developer_rating`; дамп `noHaze/bd.sql` уже содержит известные ИНН застройщиков
- `rating-service` - система оценки застройщиков из `Project`
- `nohaze-api` - API рекомендаций noHaze
- `nohaze-frontend` - React-карта

## Первый запуск

```powershell
docker compose up --build
```

После запуска можно обновлять рейтинги известных ИНН через API noHaze:

```powershell
curl -X POST "http://localhost:8000/ratings/refresh-known?limit=20"
```

## Адреса

- Фронтенд noHaze: http://localhost:3000
- API noHaze: http://localhost:8000
- API рейтинга: http://localhost:8001
- Покрытие рейтингов: http://localhost:8000/ratings/coverage

## Пересоздание БД

Данные PostgreSQL лежат в volume `postgres_data`. Чтобы начать с чистой базы:

```powershell
docker compose down -v
docker compose up --build
```
