FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# 安裝所有依賴
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec gunicorn --bind :$PORT --workers 1 main:app