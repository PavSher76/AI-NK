#!/bin/bash

# Основной скрипт развертывания AI-NK системы
set -e

echo "🚀 Развертывание AI-NK системы"
echo "=============================="

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git и повторите попытку."
    exit 1
fi

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# 1. Клонировать проект (если не существует)
if [ ! -d "AI-NK" ]; then
    echo "📥 Клонирование проекта AI-NK..."
    git clone https://github.com/PavSher76/AI-NK
    cd AI-NK
else
    echo "ℹ️  Директория AI-NK уже существует"
    cd AI-NK
fi

# 2. Генерация SSL сертификатов
echo "🔐 Проверка SSL сертификатов..."
if [ ! -f "ssl/frontend.crt" ] || [ ! -f "ssl/frontend.key" ] || [ ! -f "ssl/gateway.crt" ] || [ ! -f "ssl/gateway.key" ]; then
    echo "📜 SSL сертификаты отсутствуют, создаем новые..."
    chmod +x scripts/generate-ssl.sh
    ./scripts/generate-ssl.sh
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка при создании SSL сертификатов"
        echo "💡 Убедитесь, что OpenSSL установлен:"
        echo "   Ubuntu/Debian: sudo apt-get install openssl"
        echo "   CentOS/RHEL: sudo yum install openssl"
        echo "   macOS: brew install openssl"
        exit 1
    fi
    echo "✅ SSL сертификаты созданы успешно"
else
    echo "✅ SSL сертификаты уже существуют"
fi

# 3. Быстрое развертывание
echo "🚀 Запуск быстрого развертывания..."
./quick-deploy.sh

echo ""
echo "🎉 Развертывание AI-NK завершено!"
echo "================================"
echo ""
echo "🌐 Веб-интерфейс: https://localhost"
echo "📊 API: https://localhost:8443"
echo "🔐 Keycloak: https://localhost:8081"
echo ""
echo "⚠️  При первом запуске браузер может предупредить о самоподписанном сертификате"
echo "   Это нормально для разработки. Нажмите 'Продолжить' или 'Доверять'"
echo ""
echo "📖 Подробная документация: README.md"

