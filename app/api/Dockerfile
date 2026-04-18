FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY app/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app package
COPY app/ /app/app/

# Static fallback data for ElevenLabs agent tools (used when live dataset is empty)
COPY frontend/src/generated/location-scores.json /app/static/location-scores.json
COPY frontend/src/generated/signal-events.json /app/static/signal-events.json

ENV DATASET_DIR=/app/data
EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
