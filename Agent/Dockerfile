FROM python:3.10-slim

WORKDIR /app
COPY . /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "Agent.ragAgent_service:app", "--host", "0.0.0.0", "--port", "8000"]
