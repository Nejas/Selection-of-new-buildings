FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY noHaze/app/container-requirements.txt .
RUN pip install --no-cache-dir -r container-requirements.txt

COPY noHaze/app ./app
COPY noHaze/migrations ./migrations

WORKDIR /app/app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
