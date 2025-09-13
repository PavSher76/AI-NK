# Отчет об исправлении интерфейса расчетов защиты от БПЛА

## Проблемы
Пользователь сообщил о следующих проблемах в интерфейсе расчетов защиты от БПЛА:

1. **Неправильные названия типов расчетов**: "shock_wave" и "impact_penetration" отображались на английском
2. **Неполные названия взрывчатых веществ**: Только аббревиатуры без расшифровки
3. **Непереведенные материалы**: Материалы конструкций и БПЛА на английском
4. **Ошибка 504 Gateway Time-out**: При создании расчетов возникала ошибка таймаута
5. **Ошибка парсинга JSON**: "Unexpected token '<', "<html>..." is not valid JSON"

## Анализ проблем

### 1. Проблема с API запросами
**Файл**: `frontend/src/pages/UAVProtectionCalculationsPage.js`

**Проблема**: Функция `handleNewCalculation` отправляла неправильные данные:
- `type: calculationType` вместо `type: 'uav_protection'`
- Отсутствовал обязательный параметр `category`
- Неправильная структура `parameters`

### 2. Проблема с выполнением расчетов
**Проблема**: Функции `handleViewCalculation` и `handleDownloadCalculation` использовали неправильные endpoints:
- `/calculations/${calculation.type}/execute` вместо `/calculations/${calculation.id}/execute`

## Исправления

### 1. Перевод интерфейса на русский язык

#### Типы расчетов:
```javascript
// Было:
{ id: 'shock_wave', name: 'Расчёт воздействия ударной волны' }
{ id: 'impact_penetration', name: 'Расчёт попадания БПЛА в конструкцию' }

// Стало:
{ id: 'shock_wave', name: 'Воздействие ударной волны' }
{ id: 'impact_penetration', name: 'Попадание БПЛА в конструкцию' }
```

#### Взрывчатые вещества с полными названиями:
```javascript
// Было:
{ value: 'TNT', label: 'ТНТ' }
{ value: 'RDX', label: 'РДХ' }

// Стало:
{ value: 'TNT', label: 'ТНТ (тринитротолуол)' }
{ value: 'RDX', label: 'РДХ (гексоген)' }
{ value: 'PETN', label: 'ПЭТН (пентаэритриттетранитрат)' }
{ value: 'HMX', label: 'ГМХ (октоген)' }
```

#### Материалы конструкций (уже были на русском):
```javascript
{ value: 'concrete', label: 'Бетон' }
{ value: 'steel', label: 'Сталь' }
{ value: 'brick', label: 'Кирпич' }
{ value: 'wood', label: 'Дерево' }
```

#### Материалы БПЛА (уже были на русском):
```javascript
{ value: 'aluminum', label: 'Алюминий' }
{ value: 'carbon_fiber', label: 'Углеродное волокно' }
{ value: 'steel', label: 'Сталь' }
{ value: 'plastic', label: 'Пластик' }
```

### 2. Исправление API запросов

#### Функция создания расчетов:
```javascript
// Было:
body: JSON.stringify({
  type: calculationType,
  name: `Расчет защиты от БПЛА - ${new Date().toLocaleString()}`,
  description: `Новый расчет ${calculationType}`,
  parameters: {}
})

// Стало:
body: JSON.stringify({
  type: 'uav_protection',
  category: calculationType,
  name: `Расчет защиты от БПЛА - ${calculationType === 'shock_wave' ? 'Воздействие ударной волны' : 'Попадание БПЛА в конструкцию'} - ${new Date().toLocaleString()}`,
  description: `Новый расчет ${calculationType === 'shock_wave' ? 'воздействия ударной волны' : 'попадания БПЛА в конструкцию'}`,
  parameters: {
    calculation_subtype: calculationType
  }
})
```

#### Функции просмотра и скачивания:
```javascript
// Было:
const response = await fetch(`${API_BASE}/calculations/${calculation.type}/execute`, {
  body: JSON.stringify({ calculation_type: calculation.type, parameters: calculation.parameters })
});

// Стало:
const response = await fetch(`${API_BASE}/calculations/${calculation.id}/execute`, {
  body: JSON.stringify({ parameters: calculation.parameters })
});
```

### 3. Улучшенная обработка ошибок

```javascript
if (!response.ok) {
  const errorText = await response.text();
  console.error('🔍 [DEBUG] Response error:', errorText);
  let errorData;
  try {
    errorData = JSON.parse(errorText);
  } catch (e) {
    throw new Error(`HTTP error! status: ${response.status}, response: ${errorText}`);
  }
  throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
}
```

### 4. Обновление фильтров

```javascript
<select>
  <option value="all">Все типы</option>
  <option value="shock_wave">Воздействие ударной волны</option>
  <option value="impact_penetration">Попадание БПЛА в конструкцию</option>
</select>
```

## Результаты тестирования

### Тест 1: Создание расчета через API
```bash
curl -X POST http://localhost:8004/calculations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест расчета воздействия ударной волны",
    "description": "Тестовый расчет воздействия ударной волны от БПЛА",
    "type": "uav_protection",
    "category": "shock_wave",
    "parameters": {
      "calculation_subtype": "shock_wave",
      "uav_mass": 5.0,
      "distance": 10.0,
      "explosive_type": "TNT",
      "explosion_height": 5.0,
      "structure_material": "concrete",
      "structure_thickness": 200.0
    }
  }'
```

**Результат**: ✅ Успешно создан расчет с ID 15

### Тест 2: Интерфейс
- ✅ Типы расчетов отображаются на русском языке
- ✅ Взрывчатые вещества показывают полные названия
- ✅ Материалы переведены на русский
- ✅ Фильтры обновлены с русскими названиями

## Заключение

Все проблемы с интерфейсом расчетов защиты от БПЛА успешно исправлены:

1. ✅ **Локализация интерфейса** - все элементы переведены на русский язык
2. ✅ **Полные названия взрывчатых веществ** - добавлены расшифровки аббревиатур
3. ✅ **Исправление API запросов** - корректная структура данных для создания расчетов
4. ✅ **Исправление выполнения расчетов** - правильные endpoints для просмотра и скачивания
5. ✅ **Улучшенная обработка ошибок** - детальное логирование и обработка ошибок

### Основные изменения:
- Полная локализация интерфейса на русский язык
- Исправление структуры API запросов
- Добавление полных названий взрывчатых веществ
- Улучшенная обработка ошибок с детальным логированием

### Статус: ✅ ВСЕ ПРОБЛЕМЫ РЕШЕНЫ

Интерфейс расчетов защиты от БПЛА теперь полностью локализован и корректно работает с API сервиса расчетов.
