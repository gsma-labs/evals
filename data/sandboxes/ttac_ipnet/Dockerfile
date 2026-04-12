FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./
COPY data/devices_outputs/ ./devices_outputs/
COPY data/question_limits_config.json ./question_limits_config.json

ENV FLASK_APP=server

CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "--port", "7860"]
