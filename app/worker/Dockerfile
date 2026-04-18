FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY app/worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app package
COPY app/ /app/app/

CMD ["python", "-m", "app.worker.main"]
