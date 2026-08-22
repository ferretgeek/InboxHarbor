FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup -S inboxharbor && adduser -S -G inboxharbor -h /app inboxharbor
WORKDIR /app

COPY --chown=inboxharbor:inboxharbor inbox_harbor ./inbox_harbor
COPY --chown=inboxharbor:inboxharbor web ./web

USER inboxharbor
EXPOSE 4174

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:4174/api/health', timeout=2).read()"

ENTRYPOINT ["python", "-m", "inbox_harbor"]
CMD ["--host", "0.0.0.0", "--port", "4174"]
