# Flask web UI — local / LAN demos only (not hardened for public internet).
# Build:  docker build -t compression-web .
# Run:    docker run --rm -p 5000:5000 compression-web

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY algorithms ./algorithms
COPY utils ./utils
COPY web ./web
COPY app.py .

RUN mkdir -p uploads output

EXPOSE 5000

CMD ["python", "app.py"]
