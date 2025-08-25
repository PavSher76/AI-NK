# 📊 ПЛАН ДАШБОАРДА - OLLAMA И НОРМОКОНТРОЛЬ

## 🎯 **Цель:**
Создать комплексный дашбоард для мониторинга:
- **Статуса работы Ollama**
- **Процесса нормоконтроля**
- **Производительности системы**

## 🔧 **ТЕКУЩИЕ ВОЗМОЖНОСТИ СИСТЕМЫ:**

### **1. Ollama API:**
```json
{
  "models": [
    {
      "name": "llama3.1-optimized-v2:latest",
      "size": 4920753842,
      "details": {
        "parameter_size": "8.0B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

### **2. Нормоконтроль API:**
```json
{
  "norm_control_result": {
    "analysis_status": "uncertain",
    "total_findings": 2,
    "critical_findings": 0,
    "warning_findings": 1,
    "info_findings": 1
  }
}
```

### **3. Существующие метрики:**
- ✅ `documents` - статистика документов
- ✅ `checkable_documents` - проверяемые документы
- ✅ `elements` - извлеченные элементы
- ✅ `norm_control` - результаты нормоконтроля
- ✅ `performance` - производительность
- ✅ `reports` - отчеты

## 📈 **ПРЕДЛАГАЕМЫЕ МЕТРИКИ ДЛЯ ДАШБОАРДА:**

### **🔧 СЕКЦИЯ 1: OLLAMA STATUS**

#### **1.1 Статус сервиса Ollama:**
```json
{
  "ollama_status": {
    "service_health": "healthy/unhealthy",
    "uptime": "HH:MM:SS",
    "last_heartbeat": "2025-08-25T19:XX:XX",
    "memory_usage": "X.X GB / Y.Y GB",
    "cpu_usage": "XX.X%",
    "active_connections": 5
  }
}
```

#### **1.2 Доступные модели:**
```json
{
  "models": {
    "total_models": 3,
    "active_model": "llama3.1-optimized-v2:latest",
    "model_details": {
      "name": "llama3.1-optimized-v2:latest",
      "size_gb": 4.92,
      "parameter_size": "8.0B",
      "quantization": "Q4_K_M",
      "last_used": "2025-08-25T19:XX:XX"
    }
  }
}
```

#### **1.3 Производительность LLM:**
```json
{
  "llm_performance": {
    "requests_last_hour": 15,
    "average_response_time": "XX.X seconds",
    "success_rate": "XX.X%",
    "timeout_rate": "X.X%",
    "tokens_generated": 12500,
    "tokens_per_second": 45.2
  }
}
```

### **🔍 СЕКЦИЯ 2: НОРМОКОНТРОЛЬ**

#### **2.1 Общая статистика:**
```json
{
  "normcontrol_overview": {
    "total_documents": 3,
    "pending_reviews": 1,
    "completed_reviews": 2,
    "in_progress_reviews": 0,
    "overdue_reviews": 0,
    "success_rate": "XX.X%"
  }
}
```

#### **2.2 Результаты проверок:**
```json
{
  "normcontrol_results": {
    "total_findings": 5,
    "critical_findings": 0,
    "warning_findings": 3,
    "info_findings": 2,
    "compliance_rate": "XX.X%",
    "average_findings_per_document": 1.67
  }
}
```

#### **2.3 Производительность нормоконтроля:**
```json
{
  "normcontrol_performance": {
    "average_processing_time": "XX.X minutes",
    "documents_processed_today": 2,
    "pages_processed": 15,
    "llm_calls": 25,
    "average_llm_response_time": "XX.X seconds",
    "timeout_occurrences": 1
  }
}
```

### **📊 СЕКЦИЯ 3: ДЕТАЛЬНЫЙ ТРЕЙСЛОГ**

#### **3.1 Временные метрики:**
```json
{
  "timing_metrics": {
    "upload_time": "X.XX seconds",
    "indexing_time": "X.XX seconds",
    "llm_processing_time": "XX.XX seconds",
    "report_generation_time": "X.XX seconds",
    "total_processing_time": "XX.XX seconds"
  }
}
```

#### **3.2 Пошаговый мониторинг:**
```json
{
  "step_metrics": {
    "upload_success_rate": "100%",
    "indexing_success_rate": "100%",
    "llm_success_rate": "96%",
    "report_success_rate": "100%",
    "last_error": "httpx.ReadTimeout at 2025-08-25T19:25:00"
  }
}
```

## 🎨 **СТРУКТУРА ДАШБОАРДА:**

### **📱 Главная панель:**

#### **Верхняя строка - Статус сервисов:**
```
[🟢 Ollama] [🟢 Document Parser] [🟢 RAG Service] [🟡 Gateway]
```

#### **Секция 1 - Ollama Status:**
- **Карточка 1:** Статус сервиса (зеленый/красный индикатор)
- **Карточка 2:** Активная модель и её параметры
- **Карточка 3:** Использование ресурсов (CPU, RAM)
- **График 1:** Время ответа LLM за последние 24 часа
- **График 2:** Количество запросов к LLM

#### **Секция 2 - Нормоконтроль:**
- **Карточка 1:** Общее количество документов
- **Карточка 2:** Документы в обработке
- **Карточка 3:** Успешность проверок
- **График 1:** Находки по типам (критические/предупреждения/информация)
- **График 2:** Время обработки документов

#### **Секция 3 - Производительность:**
- **Карточка 1:** Среднее время обработки
- **Карточка 2:** Токены в секунду
- **Карточка 3:** Процент таймаутов
- **График 1:** Детальный трейслог времени
- **График 2:** Использование ресурсов

### **📊 Детальные панели:**

#### **Панель 1: Ollama Analytics**
- Детальная статистика по моделям
- История использования ресурсов
- Логи ошибок и предупреждений
- Настройки и конфигурация

#### **Панель 2: Normcontrol Analytics**
- Детальная статистика по документам
- Анализ находок по типам
- Производительность по времени суток
- Сравнение результатов

#### **Панель 3: System Performance**
- Мониторинг всех сервисов
- Сетевые метрики
- Использование диска
- Температура и вентиляция

## 🔧 **ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ:**

### **1. Новые API endpoints:**

#### **Ollama Status API:**
```python
@app.get("/api/ollama/status")
async def get_ollama_status():
    """Получение статуса Ollama"""
    return {
        "service_health": "healthy",
        "uptime": "02:15:30",
        "memory_usage": "6.2 GB / 8.0 GB",
        "cpu_usage": "45.2%",
        "active_connections": 3
    }
```

#### **Ollama Performance API:**
```python
@app.get("/api/ollama/performance")
async def get_ollama_performance():
    """Получение метрик производительности Ollama"""
    return {
        "requests_last_hour": 15,
        "average_response_time": 2.34,
        "success_rate": 96.7,
        "tokens_per_second": 45.2
    }
```

#### **Normcontrol Analytics API:**
```python
@app.get("/api/normcontrol/analytics")
async def get_normcontrol_analytics():
    """Получение аналитики нормоконтроля"""
    return {
        "total_documents": 3,
        "compliance_rate": 85.7,
        "average_findings": 1.67,
        "processing_efficiency": 92.3
    }
```

### **2. Интеграция с Prometheus:**

#### **Метрики Ollama:**
```python
# ollama_requests_total
# ollama_response_time_seconds
# ollama_memory_usage_bytes
# ollama_cpu_usage_percent
```

#### **Метрики нормоконтроля:**
```python
# normcontrol_documents_total
# normcontrol_findings_total
# normcontrol_processing_time_seconds
# normcontrol_success_rate
```

### **3. Grafana Dashboard:**

#### **Панели для Ollama:**
- **Time Series:** Время ответа LLM
- **Stat:** Статус сервиса
- **Gauge:** Использование памяти
- **Bar Chart:** Запросы по часам

#### **Панели для нормоконтроля:**
- **Time Series:** Время обработки документов
- **Pie Chart:** Распределение находок
- **Stat:** Процент соответствия
- **Table:** Последние проверки

## 🎯 **ПРЕИМУЩЕСТВА ДАШБОАРДА:**

### **1. Мониторинг в реальном времени:**
- ✅ Статус всех сервисов
- ✅ Производительность LLM
- ✅ Прогресс нормоконтроля

### **2. Проактивное управление:**
- ✅ Раннее выявление проблем
- ✅ Оптимизация ресурсов
- ✅ Планирование нагрузки

### **3. Аналитика и отчетность:**
- ✅ Тренды производительности
- ✅ Статистика качества
- ✅ ROI анализа

## 📊 **Статус:**
**📋 ПЛАН ГОТОВ - ТРЕБУЕТСЯ РЕАЛИЗАЦИЯ**

### **Следующие шаги:**
1. **Реализовать новые API endpoints**
2. **Настроить Prometheus метрики**
3. **Создать Grafana дашбоард**
4. **Протестировать и настроить алерты**

---

**Дата создания:** 25.08.2025  
**Версия:** 1.0  
**Статус:** 📋 ПЛАН ГОТОВ
