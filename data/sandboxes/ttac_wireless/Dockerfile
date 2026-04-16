FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 1000 -m -s /bin/sh app

WORKDIR /app
RUN chown app:app /app

COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app server.py _types.py utils.py ./
USER app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
