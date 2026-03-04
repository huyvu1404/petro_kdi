FROM python:3.13-slim

# Không tạo file .pyc, log ra stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài system deps (cần cho pandas/openpyxl)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8788

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8788"]
