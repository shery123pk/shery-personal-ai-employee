FROM python:3.13-slim

WORKDIR /app

# Install git for vault sync
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set cloud zone
ENV WORK_ZONE=cloud
ENV DEV_MODE=false
ENV CLOUD_HEALTH_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["python", "scripts/cloud_entrypoint.py"]
