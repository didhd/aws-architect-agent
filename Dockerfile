# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "src/app.py", "--server.port=8080", "--server.enableCORS=false"]
