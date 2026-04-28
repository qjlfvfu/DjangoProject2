FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY . .

# Сбор статики
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Используем Gunicorn вместо runserver
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]