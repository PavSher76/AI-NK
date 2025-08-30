#!/bin/bash
# Скрипт для загрузки модели gpt-oss

set -e

echo "📥 Загрузка модели gpt-oss..."

# Проверка наличия huggingface-hub
if ! command -v hf &> /dev/null; then
    echo "Устанавливаем huggingface-hub..."
    pip install huggingface-hub
fi

# Создание директории для моделей
mkdir -p models

echo "Выберите модель для загрузки:"
echo "1) gpt-oss-20b (рекомендуется для M3 Pro)"
echo "2) gpt-oss-120b (требует больше ресурсов)"
read -p "Введите номер (1 или 2): " choice

case $choice in
    1)
        echo "Загружаем gpt-oss-20b..."
        hf download openai/gpt-oss-20b --include "metal/*" --local-dir models/gpt-oss-20b/
        echo "✅ gpt-oss-20b загружен в models/gpt-oss-20b/"
        echo "🚀 Для запуска используйте:"
        echo "   python gpt_oss/metal/examples/generate.py models/gpt-oss-20b/metal/model.bin -p 'ваш_вопрос'"
        ;;
    2)
        echo "Загружаем gpt-oss-120b..."
        hf download openai/gpt-oss-120b --include "metal/*" --local-dir models/gpt-oss-120b/
        echo "✅ gpt-oss-120b загружен в models/gpt-oss-120b/"
        echo "🚀 Для запуска используйте:"
        echo "   python gpt_oss/metal/examples/generate.py models/gpt-oss-120b/metal/model.bin -p 'ваш_вопрос'"
        ;;
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac
