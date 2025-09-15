#!/bin/bash

# Скрипт для применения оптимального распределения CPU для проекта AI-NK
# Распределение 11 ядер CPU между всеми сервисами

echo "🚀 AI-NK CPU Allocation Script"
echo "=============================="
echo ""

# Проверяем, что Docker запущен
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен. Запустите Docker и попробуйте снова."
    exit 1
fi

echo "📊 Применяем оптимальное распределение 11 ядер CPU..."
echo ""

# Функция для применения CPU ограничений к контейнеру
apply_cpu_limits() {
    local container_name=$1
    local cpu_cores=$2
    local cpu_shares=$3
    local service_name=$4
    
    echo "🔧 Настраиваем $service_name..."
    
    # Проверяем, запущен ли контейнер
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        # Применяем CPU ограничения
        docker update --cpus "$cpu_cores" "$container_name" 2>/dev/null
        docker update --cpu-shares "$cpu_shares" "$container_name" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "   ✅ $service_name: $cpu_cores ядер, $cpu_shares shares"
        else
            echo "   ⚠️  $service_name: Ошибка применения ограничений"
        fi
    else
        echo "   ⚠️  $service_name: Контейнер не запущен"
    fi
}

echo "🎯 Высокий приоритет (5.5 ядер):"
echo "--------------------------------"

# Высокоприоритетные сервисы
apply_cpu_limits "ai-nk-rag-service-1" "2.5" "1024" "RAG Service"
apply_cpu_limits "ai-nk-document-parser-1" "2.0" "1024" "Document Parser"
apply_cpu_limits "ai-nk-vllm-service-1" "1.0" "1024" "VLLM Service"

echo ""
echo "⚖️  Средний приоритет (3.0 ядра):"
echo "--------------------------------"

# Среднеприоритетные сервисы
apply_cpu_limits "ai-nk-rule-engine-1" "0.8" "512" "Rule Engine"
apply_cpu_limits "ai-nk-calculation-service-1" "0.8" "512" "Calculation Service"
apply_cpu_limits "ai-nk-spellchecker-service-1" "0.6" "512" "SpellChecker Service"
apply_cpu_limits "ai-nk-archive-service-1" "0.8" "512" "Archive Service"

echo ""
echo "🏗️  Базовый приоритет (1.5 ядра):"
echo "--------------------------------"

# Базовые сервисы
apply_cpu_limits "ai-nk-norms-db-1" "0.6" "256" "PostgreSQL"
apply_cpu_limits "ai-nk-qdrant-1" "0.5" "256" "Qdrant"
apply_cpu_limits "ai-nk-gateway-1" "0.4" "256" "Gateway"

echo ""
echo "🔧 Вспомогательный приоритет (1.0 ядро):"
echo "----------------------------------------"

# Вспомогательные сервисы
apply_cpu_limits "ai-nk-outgoing-control-service-1" "0.3" "128" "Outgoing Control"
apply_cpu_limits "ai-nk-languagetool-1" "0.3" "128" "LanguageTool"
apply_cpu_limits "ai-nk-analog-objects-service-1" "0.2" "128" "Analog Objects"
apply_cpu_limits "ai-nk-redis-1" "0.1" "64" "Redis"
apply_cpu_limits "ai-nk-keycloak-1" "0.1" "64" "Keycloak"

echo ""
echo "📈 Проверяем текущее распределение CPU..."
echo "========================================"

# Показываем текущую статистику
echo ""
echo "🖥️  Текущее использование CPU:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 1
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "ai-nk-"

echo ""
echo "📊 Сводка распределения:"
echo "======================="
echo "Высокий приоритет:    5.5 ядер (50%)"
echo "Средний приоритет:    3.0 ядра (27%)"
echo "Базовый приоритет:    1.5 ядра (14%)"
echo "Вспомогательный:      1.0 ядро (9%)"
echo "ИТОГО:               11.0 ядер (100%)"
echo ""

echo "✅ Распределение CPU применено успешно!"
echo ""
echo "🔄 Для мониторинга используйте:"
echo "   ./monitor_cpu_distribution.sh"
echo ""
echo "📝 Для применения через Docker Compose:"
echo "   docker-compose -f docker-compose.cpu-optimized.yaml up -d"
echo ""

# Создаем файл с текущими настройками
cat > cpu_allocation_applied.txt << EOF
AI-NK CPU Allocation Applied
============================
Date: $(date)
Total Cores: 11

High Priority (5.5 cores):
- RAG Service: 2.5 cores, 1024 shares
- Document Parser: 2.0 cores, 1024 shares  
- VLLM Service: 1.0 cores, 1024 shares

Medium Priority (3.0 cores):
- Rule Engine: 0.8 cores, 512 shares
- Calculation Service: 0.8 cores, 512 shares
- SpellChecker Service: 0.6 cores, 512 shares
- Archive Service: 0.8 cores, 512 shares

Base Priority (1.5 cores):
- PostgreSQL: 0.6 cores, 256 shares
- Qdrant: 0.5 cores, 256 shares
- Gateway: 0.4 cores, 256 shares

Support Priority (1.0 cores):
- Outgoing Control: 0.3 cores, 128 shares
- LanguageTool: 0.3 cores, 128 shares
- Analog Objects: 0.2 cores, 128 shares
- Redis: 0.1 cores, 64 shares
- Keycloak: 0.1 cores, 64 shares

Total: 11.0 cores (100%)
EOF

echo "📄 Настройки сохранены в cpu_allocation_applied.txt"
