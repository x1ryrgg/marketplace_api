FROM python:3.13-slim

WORKDIR /app

# Install system dependencies first
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=marketplace_api.settings

CMD python manage.py makemigrations \
    && python manage.py migrate \
    && python manage.py collectstatic --no-input \
    && python manage.py createcachetable \
    && ["gunicorn", "marketplace_api.wsgi:application", "--bind", "0.0.0.0:8000"]