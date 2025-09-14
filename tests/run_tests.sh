#!/bin/bash
# Скрипт для быстрого запуска тестов AI-NK

echo "🚀 Запуск тестирования AI-NK..."
echo "=================================="

# Проверка наличия виртуального окружения
if [ ! -d "test_env" ]; then
    echo "❌ Виртуальное окружение не найдено. Создаю..."
    python3 -m venv test_env
    source test_env/bin/activate
    pip install aiohttp
else
    echo "✅ Виртуальное окружение найдено"
    source test_env/bin/activate
fi

# Проверка наличия скриптов
if [ ! -f "scripts/run_comprehensive_tests.py" ]; then
    echo "❌ Скрипты тестирования не найдены"
    exit 1
fi

# Создание необходимых папок
mkdir -p reports logs

# Запуск тестов
echo "🧪 Запуск комплексного тестирования..."
python scripts/run_comprehensive_tests.py

# Проверка результата
if [ $? -eq 0 ]; then
    echo "✅ Тестирование завершено успешно"
else
    echo "❌ Тестирование завершено с ошибками"
fi

echo "📄 Отчеты сохранены в папке reports/"
echo "📋 Логи сохранены в папке logs/"
