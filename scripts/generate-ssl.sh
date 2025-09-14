#!/bin/bash

# Скрипт для генерации SSL сертификатов для AI-NK системы
# Создает самоподписанные сертификаты для разработки и тестирования

set -e

echo "🔐 Генерация SSL сертификатов для AI-NK системы"
echo "=============================================="

# Создание директории SSL если не существует
SSL_DIR="ssl"
if [ ! -d "$SSL_DIR" ]; then
    echo "📁 Создание директории $SSL_DIR..."
    mkdir -p "$SSL_DIR"
    chmod 700 "$SSL_DIR"
fi

# Функция для генерации сертификата
generate_certificate() {
    local name=$1
    local subject=$2
    local san=$3
    
    echo "🔧 Генерация сертификата для $name..."
    
    # Генерация приватного ключа
    openssl genrsa -out "$SSL_DIR/${name}.key" 2048
    chmod 600 "$SSL_DIR/${name}.key"
    
    # Создание конфигурации для SAN
    local config_file="$SSL_DIR/${name}.conf"
    cat > "$config_file" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=RU
ST=Moscow
L=Moscow
O=AI-NK
OU=Development
CN=$subject

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = $san
EOF

    # Генерация сертификата
    openssl req -new -x509 -key "$SSL_DIR/${name}.key" -out "$SSL_DIR/${name}.crt" \
        -days 365 -config "$config_file" -extensions v3_req
    
    # Удаление временного конфигурационного файла
    rm -f "$config_file"
    
    echo "✅ Сертификат $name создан успешно"
}

# Проверка наличия OpenSSL
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL не установлен. Установите OpenSSL и повторите попытку."
    echo "   Ubuntu/Debian: sudo apt-get install openssl"
    echo "   CentOS/RHEL: sudo yum install openssl"
    echo "   macOS: brew install openssl"
    exit 1
fi

echo "✅ OpenSSL найден: $(openssl version)"

# Генерация сертификатов для различных сервисов

# 1. Frontend сертификат
if [ ! -f "$SSL_DIR/frontend.crt" ] || [ ! -f "$SSL_DIR/frontend.key" ]; then
    generate_certificate "frontend" "localhost" "DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1,IP:0.0.0.0"
else
    echo "ℹ️  Frontend сертификат уже существует"
fi

# 2. Gateway сертификат
if [ ! -f "$SSL_DIR/gateway.crt" ] || [ ! -f "$SSL_DIR/gateway.key" ]; then
    generate_certificate "gateway" "gateway.localhost" "DNS:gateway.localhost,DNS:localhost,IP:127.0.0.1"
else
    echo "ℹ️  Gateway сертификат уже существует"
fi

# 3. Keycloak сертификат
if [ ! -f "$SSL_DIR/keycloak.crt" ] || [ ! -f "$SSL_DIR/keycloak.key" ]; then
    generate_certificate "keycloak" "keycloak.localhost" "DNS:keycloak.localhost,DNS:localhost,IP:127.0.0.1"
else
    echo "ℹ️  Keycloak сертификат уже существует"
fi

# 4. Создание Keycloak keystore (если не существует)
if [ ! -f "$SSL_DIR/keycloak.keystore" ]; then
    echo "🔧 Создание Keycloak keystore..."
    
    # Конвертация сертификата в PKCS12
    openssl pkcs12 -export -in "$SSL_DIR/keycloak.crt" -inkey "$SSL_DIR/keycloak.key" \
        -out "$SSL_DIR/keycloak.p12" -name "keycloak" -password pass:changeit
    
    # Создание Java keystore
    keytool -importkeystore -deststorepass changeit -destkeypass changeit \
        -destkeystore "$SSL_DIR/keycloak.keystore" -srckeystore "$SSL_DIR/keycloak.p12" \
        -srcstoretype PKCS12 -srcstorepass changeit -alias keycloak
    
    echo "✅ Keycloak keystore создан успешно"
else
    echo "ℹ️  Keycloak keystore уже существует"
fi

# 5. Создание корневого CA сертификата (опционально)
if [ ! -f "$SSL_DIR/ca.crt" ] || [ ! -f "$SSL_DIR/ca.key" ]; then
    echo "🔧 Создание корневого CA сертификата..."
    
    # Генерация CA ключа
    openssl genrsa -out "$SSL_DIR/ca.key" 4096
    chmod 600 "$SSL_DIR/ca.key"
    
    # Создание CA сертификата
    openssl req -new -x509 -key "$SSL_DIR/ca.key" -out "$SSL_DIR/ca.crt" \
        -days 3650 -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-NK/OU=CA/CN=AI-NK Root CA"
    
    echo "✅ Корневой CA сертификат создан успешно"
else
    echo "ℹ️  Корневой CA сертификат уже существует"
fi

# Установка правильных прав доступа
echo "🔧 Настройка прав доступа..."
chmod 600 "$SSL_DIR"/*.key
chmod 644 "$SSL_DIR"/*.crt
chmod 644 "$SSL_DIR"/*.keystore
chmod 644 "$SSL_DIR"/*.p12

# Проверка сертификатов
echo "🔍 Проверка созданных сертификатов..."
for cert in frontend gateway keycloak; do
    if [ -f "$SSL_DIR/${cert}.crt" ] && [ -f "$SSL_DIR/${cert}.key" ]; then
        echo "✅ $cert: $(openssl x509 -in "$SSL_DIR/${cert}.crt" -noout -subject -dates 2>/dev/null | head -1)"
    else
        echo "❌ $cert: сертификат или ключ отсутствует"
    fi
done

echo ""
echo "🎉 Генерация SSL сертификатов завершена!"
echo "======================================"
echo ""
echo "📁 Сертификаты созданы в директории: $SSL_DIR/"
echo ""
echo "📋 Созданные файлы:"
echo "  • frontend.crt / frontend.key - для веб-интерфейса"
echo "  • gateway.crt / gateway.key - для API Gateway"
echo "  • keycloak.crt / keycloak.key - для Keycloak"
echo "  • keycloak.keystore - Java keystore для Keycloak"
echo "  • ca.crt / ca.key - корневой CA сертификат"
echo ""
echo "⚠️  ВАЖНО: Это самоподписанные сертификаты для разработки!"
echo "   Для продакшена используйте сертификаты от доверенного CA"
echo ""
echo "🔧 Для добавления доверия к сертификатам:"
echo "   • macOS: Добавьте ca.crt в Keychain Access"
echo "   • Linux: sudo cp ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates"
echo "   • Windows: Импортируйте ca.crt в Trusted Root Certification Authorities"
echo ""
echo "🚀 Теперь можно запускать систему с HTTPS!"
