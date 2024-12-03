# Dockerfile
FROM python:3.11-slim

# Installing system's dependensies
RUN apt-get update && apt-get install -y gcc libpq-dev

# Installing Python's dependensies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Coping the app's code
COPY . .

# Installing invironment for FastAPI
ENV PYTHONUNBUFFERED=1

# Running FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
