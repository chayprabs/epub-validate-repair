FROM python:3.12-slim-bookworm

ARG EPUBCHECK_VERSION=5.2.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EPUBDOCTOR_EPUBCHECK_JAR=/opt/epubcheck/epubcheck.jar

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        calibre \
        curl \
        openjdk-17-jre-headless \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/epubcheck \
    && curl -fsSL -o /tmp/epubcheck.zip "https://github.com/w3c/epubcheck/releases/download/v${EPUBCHECK_VERSION}/epubcheck-${EPUBCHECK_VERSION}.zip" \
    && unzip -q /tmp/epubcheck.zip -d /opt/epubcheck-dist \
    && cp /opt/epubcheck-dist/epubcheck-${EPUBCHECK_VERSION}/epubcheck.jar /opt/epubcheck/epubcheck.jar \
    && rm -rf /tmp/epubcheck.zip /opt/epubcheck-dist

COPY apps/worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/worker/src ./src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
