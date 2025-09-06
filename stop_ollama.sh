#!/bin/bash

# Скрипт остановки Ollama
# Использование: ./stop_ollama.sh

echo "🛑 [OLLAMA_STOP] Останавливаем Ollama..."

# Останавливаем по PID файлу
if [ -f "ollama.pid" ]; then
    PID=$(cat ollama.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Ollama остановлен (PID: $PID)"
        rm -f ollama.pid
    else
        echo "⚠️ Процесс с PID $PID не найден"
        rm -f ollama.pid
    fi
fi

# Дополнительная проверка и остановка
if pgrep -f "ollama serve" > /dev/null; then
    echo "🔄 Останавливаем все процессы Ollama..."
    pkill -f "ollama serve"
    sleep 2
    echo "✅ Все процессы Ollama остановлены"
else
    echo "ℹ️ Ollama не запущен"
fi

echo "✅ Остановка завершена"
