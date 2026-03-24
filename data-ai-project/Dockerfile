FROM python:3.13-slim-bullseye

RUN apt-get update && apt-get install -y build-essential gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install uv==0.9.7 \
    && uv pip install --system -r requirements.txt

COPY .mypy.ini .
COPY src/ ./src/
