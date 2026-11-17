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

## Настройка доступа

Скопируйте `.env.example` в `.env`, задайте уникальный длинный пароль PostgreSQL
(латинские буквы и цифры) и отдельный случайный `NEWS_ADMIN_KEY`. Файл `.env`
не должен попадать в систему контроля версий. Порт PostgreSQL доступен только
контейнерам внутренней сети. Для добавления и переключения источников передайте
ключ в заголовке `X-News-Admin-Key`; без настроенного ключа изменения запрещены.
Разрешены HTTPS-адреса `news.google.com` и `www.vedomosti.ru`; для других
проверенных источников потребуется дополнить список в `Project/news_url.py`.
Перенаправления источников отключены.

Досье хранится в кеше в течение `DOSSIER_TTL_HOURS` часов (по умолчанию 24),
после чего рассчитывается заново. В ответе указано время расчёта в UTC.

Если volume базы уже существует, изменение `.env` не меняет пароль PostgreSQL.
Сначала обновите пароль пользователя `postgres` в существующей базе штатными
средствами PostgreSQL, затем укажите тот же пароль в `.env` и перезапустите
контейнеры. Не удаляйте volume, если данные нужно сохранить.
