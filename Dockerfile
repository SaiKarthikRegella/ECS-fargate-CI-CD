FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash appuser  && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=2)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", \
     "--access-logfile", "-", "--error-logfile", "-", "--preload",\
     "app:create_app()"]