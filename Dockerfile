FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY sdanalyzer/ sdanalyzer/
COPY web_app.py cli.py ./

# Non-root, no writable data dir needed: the app never writes uploads to disk
RUN useradd -m appuser
USER appuser

ENV HOST=0.0.0.0 PORT=5080
EXPOSE 5080

CMD ["sh", "-c", "gunicorn --bind ${HOST}:${PORT} --workers 1 --threads 4 --timeout 120 web_app:app"]
