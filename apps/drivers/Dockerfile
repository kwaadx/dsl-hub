FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./

ENV QUEUE_OUTBOX=/queue/outbox     DRIVER_OUT=/queue/driver_out     POLL_INTERVAL_MS=500

RUN mkdir -p /queue/outbox /queue/driver_out
VOLUME ["/queue"]

CMD ["python", "-u", "main.py"]
