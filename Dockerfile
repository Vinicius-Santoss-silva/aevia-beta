# Hospedagem com disco persistente. Leia docs/PUBLICACAO_COM_DOCKER.md.
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000 DB_PATH=/data/aevia.sqlite3 STORAGE_DIR=/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home aevia && mkdir -p /data && chown aevia:aevia /data
COPY --chown=aevia:aevia . .
USER aevia
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=50s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:'+__import__('os').environ.get('PORT','10000')+'/healthz',timeout=4)" || exit 1
CMD ["sh", "-c", "python -m app.sync_data && exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
