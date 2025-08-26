FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn httpx

COPY ollama_adapter_optimized.py ./ollama_adapter.py

# Оптимизированные переменные окружения для MacBook Pro
ENV OLLAMA_CPU_THREADS=10
ENV OLLAMA_GPU_LAYERS=0
ENV OLLAMA_BATCH_SIZE=1

EXPOSE 8000

CMD ["uvicorn", "ollama_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
