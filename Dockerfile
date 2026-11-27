FROM python:3.12-alpine AS base

RUN apk upgrade --no-cache

FROM base AS builder

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM base AS runtime

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN addgroup -g 10001 devops && \
    adduser -D -u 10001 -G devops devops

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app.py .
COPY src/ src/
COPY templates/ templates/

USER devops

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
