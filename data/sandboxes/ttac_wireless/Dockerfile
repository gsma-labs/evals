FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py _types.py utils.py ./

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
