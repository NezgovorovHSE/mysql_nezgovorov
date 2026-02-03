FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы из текущей папки
COPY requirements.txt .
COPY generate_orders.py .
COPY generator.py .

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs /app/generated_data

# Файлы из app/ не нужны для генератора