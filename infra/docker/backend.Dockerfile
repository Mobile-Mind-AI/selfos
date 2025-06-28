FROM python:3.11-slim
WORKDIR /app
COPY apps/backend-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/backend-api /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]