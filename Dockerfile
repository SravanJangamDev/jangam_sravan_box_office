FROM python:3.12-slim

WORKDIR /app

COPY src/ ./src/

RUN pip install --upgrade pip
RUN pip install -r src/requirements.txt

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.app:app --host 0.0.0.0 --port 8000"]
