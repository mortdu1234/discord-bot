FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances d'abord (meilleur cache Docker : réinstallées seulement si requirements.txt change)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Exécution sans les droits root
RUN mkdir -p /app/data && useradd --create-home --uid 1000 bot && chown -R bot:bot /app
USER bot

CMD ["python", "main.py"]
