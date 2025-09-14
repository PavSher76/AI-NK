#!/bin/bash

# Скрипт для обновления SSL сертификатов AI-NK системы
# Используется для продления срока действия или пересоздания сертификатов

set -e

echo "🔄 Обновление SSL сертификатов AI-NK системы"
echo "==========================================="

# Проверка наличия OpenSSL
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL не установлен. Установите OpenSSL и повторите попытку."
    echo "   Ubuntu/Debian: sudo apt-get install openssl"
    echo "   CentOS/RHEL: sudo yum install openssl"
    echo "   macOS: brew install openssl"
    exit 1
fi

# Создание резервной копии существующих сертификатов
SSL_DIR="ssl"
BACKUP_DIR="ssl/backup-$(date +%Y%m%d-%H%M%S)"

if [ -d "$SSL_DIR" ] && [ "$(ls -A $SSL_DIR 2>/dev/null)" ]; then
    echo "💾 Создание резервной копии существующих сертификатов..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$SSL_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
    echo "✅ Резервная копия создана в $BACKUP_DIR/"
fi

# Остановка системы перед обновлением сертификатов
echo "🛑 Остановка системы для обновления сертификатов..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose не найден"
    exit 1
fi

$COMPOSE_CMD down 2>/dev/null || true

# Генерация новых сертификатов
echo "🔐 Генерация новых SSL сертификатов..."
./scripts/generate-ssl.sh

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при создании новых сертификатов"
    echo "🔄 Восстановление из резервной копии..."
    if [ -d "$BACKUP_DIR" ]; then
        cp -r "$BACKUP_DIR"/* "$SSL_DIR/" 2>/dev/null || true
    fi
    exit 1
fi

# Проверка новых сертификатов
echo "🔍 Проверка новых сертификатов..."
for cert in frontend gateway keycloak; do
    if [ -f "$SSL_DIR/${cert}.crt" ] && [ -f "$SSL_DIR/${cert}.key" ]; then
        echo "✅ $cert: $(openssl x509 -in "$SSL_DIR/${cert}.crt" -noout -subject -dates 2>/dev/null | head -1)"
    else
        echo "❌ $cert: сертификат или ключ отсутствует"
    fi
done

# Запуск системы с новыми сертификатами
echo "🚀 Запуск системы с новыми сертификатами..."
$COMPOSE_CMD up -d

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при запуске системы"
    echo "🔄 Восстановление из резервной копии..."
    if [ -d "$BACKUP_DIR" ]; then
        cp -r "$BACKUP_DIR"/* "$SSL_DIR/" 2>/dev/null || true
    fi
    $COMPOSE_CMD up -d
    exit 1
fi

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 30

# Проверка состояния системы
echo "🔍 Проверка состояния системы..."
if curl -f -k https://localhost/health >/dev/null 2>&1; then
    echo "✅ Система запущена успешно с новыми сертификатами"
else
    echo "⚠️  Система может быть еще не готова, проверьте через несколько минут"
fi

echo ""
echo "🎉 Обновление SSL сертификатов завершено!"
echo "======================================="
echo ""
echo "📁 Новые сертификаты: $SSL_DIR/"
echo "💾 Резервная копия: $BACKUP_DIR/"
echo ""
echo "🌐 Веб-интерфейс: https://localhost"
echo "📊 API: https://localhost:8443"
echo "🔐 Keycloak: https://localhost:8081"
echo ""
echo "⚠️  При первом запуске браузер может предупредить о новом сертификате"
echo "   Очистите кэш браузера или добавьте новый CA сертификат в доверенные"
echo ""
echo "🗑️  Для удаления резервной копии: rm -rf $BACKUP_DIR"
