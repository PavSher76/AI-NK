#!/bin/bash

# Скрипт для мониторинга распределения CPU между контейнерами
# AI-NK CPU Distribution Monitor

echo "🚀 AI-NK CPU Distribution Monitor"
echo "=================================="
echo ""

# Функция для отображения CPU статистики контейнера
show_container_cpu() {
    local container_name=$1
    local service_name=$2
    local priority=$3
    
    echo "📊 $service_name ($priority)"
    echo "   Container: $container_name"
    
    # Получаем статистику CPU
    local cpu_stats=$(docker stats --no-stream --format "table {{.CPUPerc}}" $container_name 2>/dev/null | tail -n 1)
    
    if [ $? -eq 0 ] && [ ! -z "$cpu_stats" ]; then
        echo "   Current CPU: $cpu_stats"
        
        # Получаем информацию о лимитах
        local cpu_limit=$(docker inspect $container_name --format='{{.HostConfig.CpuQuota}}' 2>/dev/null)
        local cpu_period=$(docker inspect $container_name --format='{{.HostConfig.CpuPeriod}}' 2>/dev/null)
        
        if [ "$cpu_limit" != "0" ] && [ "$cpu_period" != "0" ]; then
            local cpu_limit_calc=$(echo "scale=2; $cpu_limit / $cpu_period" | bc 2>/dev/null || echo "N/A")
            echo "   CPU Limit: ${cpu_limit_calc} cores"
        else
            echo "   CPU Limit: No limit"
        fi
        
        # Получаем информацию о резервах и shares
        local cpu_reservation=$(docker inspect $container_name --format='{{.HostConfig.CpuShares}}' 2>/dev/null)
        if [ "$cpu_reservation" != "0" ]; then
            echo "   CPU Shares: $cpu_reservation"
        fi
        
        # Получаем информацию о CPU reservation
        local cpu_reservation_cores=$(docker inspect $container_name --format='{{.HostConfig.CpuReservation}}' 2>/dev/null)
        if [ "$cpu_reservation_cores" != "0" ]; then
            echo "   CPU Reservation: ${cpu_reservation_cores} cores"
        fi
    else
        echo "   Status: Container not running or not found"
    fi
    echo ""
}

# Проверяем, запущены ли контейнеры
echo "🔍 Checking running containers..."
echo ""

# Основные сервисы с высоким приоритетом
show_container_cpu "ai-nk-rag-service-1" "RAG Service" "HIGH PRIORITY"
show_container_cpu "ai-nk-document-parser-1" "Document Parser" "HIGH PRIORITY"

echo "---"
echo ""

# Сервисы со средним приоритетом
show_container_cpu "ai-nk-vllm-1" "VLLM Service" "MEDIUM PRIORITY"
show_container_cpu "ai-nk-rule-engine-1" "Rule Engine" "MEDIUM PRIORITY"
show_container_cpu "ai-nk-calculation-service-1" "Calculation Service" "MEDIUM PRIORITY"

echo "---"
echo ""

# Базовые сервисы
show_container_cpu "ai-nk-norms-db-1" "PostgreSQL Database" "BASE SERVICE"
show_container_cpu "ai-nk-qdrant-1" "Qdrant Vector DB" "BASE SERVICE"
show_container_cpu "ai-nk-gateway-1" "API Gateway" "BASE SERVICE"

echo "---"
echo ""

# Вспомогательные сервисы
show_container_cpu "ai-nk-redis-1" "Redis Cache" "SUPPORT SERVICE"
show_container_cpu "ai-nk-prometheus-1" "Prometheus" "SUPPORT SERVICE"
show_container_cpu "ai-nk-grafana-1" "Grafana" "SUPPORT SERVICE"

echo "=================================="
echo "📈 CPU Distribution Summary:"
echo ""

# Общая статистика системы
echo "🖥️  System CPU Usage:"
top -l 1 | grep "CPU usage" || echo "   Unable to get system CPU usage"

echo ""
echo "📊 Docker CPU Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 1
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "ai-nk-"

echo ""
echo "🎯 Expected CPU Distribution (11 cores total):"
echo ""
echo "🚀 HIGH PRIORITY (5.5 cores):"
echo "   RAG Service: 1024 shares, 2.5 cores - 22.7%"
echo "   Document Parser: 1024 shares, 2.0 cores - 18.2%"
echo "   VLLM Service: 1024 shares, 1.0 cores - 9.1%"
echo ""
echo "⚖️  MEDIUM PRIORITY (3.0 cores):"
echo "   Rule Engine: 512 shares, 0.8 cores - 7.3%"
echo "   Calculation Service: 512 shares, 0.8 cores - 7.3%"
echo "   SpellChecker Service: 512 shares, 0.6 cores - 5.5%"
echo "   Archive Service: 512 shares, 0.8 cores - 7.3%"
echo ""
echo "🏗️  BASE PRIORITY (1.5 cores):"
echo "   PostgreSQL: 256 shares, 0.6 cores - 5.5%"
echo "   Qdrant: 256 shares, 0.5 cores - 4.5%"
echo "   Gateway: 256 shares, 0.4 cores - 3.6%"
echo ""
echo "🔧 SUPPORT PRIORITY (1.0 cores):"
echo "   Outgoing Control: 128 shares, 0.3 cores - 2.7%"
echo "   LanguageTool: 128 shares, 0.3 cores - 2.7%"
echo "   Analog Objects: 128 shares, 0.2 cores - 1.8%"
echo "   Redis: 64 shares, 0.1 cores - 0.9%"
echo "   Keycloak: 64 shares, 0.1 cores - 0.9%"
echo ""
echo "✅ Total allocated: 11.0 cores (100%)"
echo "✅ CPU Shares: High (1024) > Medium (512) > Base (256) > Support (64-128)"
echo "ℹ️  Note: macOS Docker uses CPU shares instead of hard limits"
echo ""
echo "🔄 Run this script every 30 seconds to monitor:"
echo "   watch -n 30 ./monitor_cpu_distribution.sh"
