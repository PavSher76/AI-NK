FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn httpx

COPY ollama_adapter.py .

EXPOSE 8000

CMD ["uvicorn", "ollama_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
