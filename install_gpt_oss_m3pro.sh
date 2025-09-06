#!/bin/bash

# Скрипт установки gpt-oss для M3 Pro локально вне Docker
# Автор: AI Assistant
# Дата: $(date)

set -e  # Остановка при ошибке

echo "🚀 Установка gpt-oss для M3 Pro локально вне Docker"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка системы
log_info "Проверка системы..."

# Проверка macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "Этот скрипт предназначен только для macOS"
    exit 1
fi

# Проверка архитектуры
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    log_warning "Рекомендуется использовать Apple Silicon (M1/M2/M3)"
fi

log_success "Система: macOS $(sw_vers -productVersion) на $ARCH"

# Проверка Python
log_info "Проверка Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    log_error "Требуется Python 3.12 или выше. Текущая версия: $PYTHON_VERSION"
    exit 1
fi
log_success "Python версия: $PYTHON_VERSION"

# Проверка uv
log_info "Проверка uv..."
if ! command -v uv &> /dev/null; then
    log_error "uv не установлен. Установите uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
log_success "uv установлен: $(uv --version)"

# Проверка Xcode CLI tools
log_info "Проверка Xcode CLI tools..."
if ! xcode-select -p &> /dev/null; then
    log_warning "Xcode CLI tools не установлены. Устанавливаем..."
    xcode-select --install
    echo "Пожалуйста, завершите установку Xcode CLI tools и запустите скрипт снова"
    exit 1
fi
log_success "Xcode CLI tools установлены"

# Проверка git
log_info "Проверка git..."
if ! command -v git &> /dev/null; then
    log_error "git не установлен"
    exit 1
fi
log_success "git установлен: $(git --version)"

# Создание виртуального окружения
log_info "Создание виртуального окружения..."
if [ -d "gpt_oss_env" ]; then
    log_warning "Виртуальное окружение уже существует. Удаляем..."
    rm -rf gpt_oss_env
fi

uv venv gpt_oss_env
log_success "Виртуальное окружение создано"

# Активация виртуального окружения
log_info "Активация виртуального окружения..."
source gpt_oss_env/bin/activate
log_success "Виртуальное окружение активировано"

# Обновление pip
log_info "Обновление pip..."
uv pip install --upgrade pip
log_success "pip обновлен"

# Клонирование gpt-oss
log_info "Клонирование gpt-oss..."
if [ -d "gpt-oss" ]; then
    log_warning "Репозиторий gpt-oss уже существует. Обновляем..."
    cd gpt-oss
    git pull origin main
    cd ..
else
    git clone https://github.com/openai/gpt-oss.git
    log_success "gpt-oss клонирован"
fi

# Переход в директорию gpt-oss
cd gpt-oss

# Установка зависимостей для Metal
log_info "Установка gpt-oss с Metal бэкендом..."
export GPTOSS_BUILD_METAL=1
uv pip install -e ".[metal]"

if [ $? -eq 0 ]; then
    log_success "gpt-oss с Metal бэкендом установлен успешно"
else
    log_error "Ошибка при установке gpt-oss"
    exit 1
fi

# Возврат в корневую директорию
cd ..

# Создание скрипта для активации окружения
log_info "Создание скрипта активации..."
cat > activate_gpt_oss.sh << 'EOF'
#!/bin/bash
# Скрипт для активации окружения gpt-oss
echo "🔧 Активация окружения gpt-oss..."
source gpt_oss_env/bin/activate
echo "✅ Окружение gpt-oss активировано"
echo "📁 Текущая директория: $(pwd)"
echo "🐍 Python: $(which python)"
echo "📦 gpt-oss установлен в: $(pip show gpt-oss | grep Location | cut -d' ' -f2)"
echo ""
echo "🚀 Для запуска gpt-oss используйте:"
echo "   python -m gpt_oss.chat --backend metal <путь_к_модели>"
echo ""
EOF

chmod +x activate_gpt_oss.sh
log_success "Скрипт активации создан: activate_gpt_oss.sh"

# Создание скрипта для загрузки модели
log_info "Создание скрипта загрузки модели..."
cat > download_gpt_oss_model.sh << 'EOF'
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
EOF

chmod +x download_gpt_oss_model.sh
log_success "Скрипт загрузки модели создан: download_gpt_oss_model.sh"

# Создание тестового скрипта
log_info "Создание тестового скрипта..."
cat > test_gpt_oss.py << 'EOF'
#!/usr/bin/env python3
"""
Тестовый скрипт для проверки установки gpt-oss
"""

import sys
import os

def test_imports():
    """Тест импорта модулей gpt-oss"""
    try:
        import gpt_oss
        print("✅ gpt_oss импортирован успешно")
        
        # Проверка доступных модулей
        modules = ['torch', 'metal', 'tools']
        for module in modules:
            try:
                __import__(f'gpt_oss.{module}')
                print(f"✅ gpt_oss.{module} доступен")
            except ImportError as e:
                print(f"⚠️  gpt_oss.{module} недоступен: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта gpt_oss: {e}")
        return False

def test_metal_backend():
    """Тест Metal бэкенда"""
    try:
        from gpt_oss.metal import model
        print("✅ Metal бэкенд доступен")
        return True
    except ImportError as e:
        print(f"❌ Metal бэкенд недоступен: {e}")
        return False

def main():
    print("🧪 Тестирование установки gpt-oss")
    print("=" * 40)
    
    # Тест импортов
    imports_ok = test_imports()
    
    # Тест Metal бэкенда
    metal_ok = test_metal_backend()
    
    print("\n" + "=" * 40)
    if imports_ok and metal_ok:
        print("🎉 Все тесты пройдены! gpt-oss установлен корректно")
        print("\n📋 Следующие шаги:")
        print("1. Запустите: ./download_gpt_oss_model.sh")
        print("2. Активируйте окружение: source activate_gpt_oss.sh")
        print("3. Запустите модель: python gpt_oss/metal/examples/generate.py <путь_к_модели> -p 'ваш_вопрос'")
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x test_gpt_oss.py
log_success "Тестовый скрипт создан: test_gpt_oss.py"

# Создание README
log_info "Создание README..."
cat > GPT_OSS_README.md << 'EOF'
# Установка gpt-oss для M3 Pro

## Обзор
Этот проект содержит установленную локально версию gpt-oss (OpenAI's open-weight models) для Apple Silicon (M3 Pro).

## Структура проекта
```
.
├── gpt_oss_env/           # Виртуальное окружение Python
├── gpt-oss/              # Репозиторий gpt-oss
├── models/               # Директория для моделей (создается при загрузке)
├── activate_gpt_oss.sh   # Скрипт активации окружения
├── download_gpt_oss_model.sh  # Скрипт загрузки модели
├── test_gpt_oss.py       # Тестовый скрипт
└── GPT_OSS_README.md     # Этот файл
```

## Быстрый старт

### 1. Активация окружения
```bash
source activate_gpt_oss.sh
```

### 2. Тестирование установки
```bash
python test_gpt_oss.py
```

### 3. Загрузка модели
```bash
./download_gpt_oss_model.sh
```

### 4. Запуск модели
```bash
# Для gpt-oss-20b
python gpt-oss/gpt_oss/metal/examples/generate.py models/gpt-oss-20b/metal/model.bin -p "Привет, как дела?"

# Для gpt-oss-120b
python gpt-oss/gpt_oss/metal/examples/generate.py models/gpt-oss-120b/metal/model.bin -p "Привет, как дела?"
```

## Использование в чате

### Терминальный чат
```bash
# Активируйте окружение
source activate_gpt_oss.sh

# Запустите чат с моделью
python -m gpt_oss.chat --backend metal models/gpt-oss-20b/metal/model.bin
```

### С инструментами
```bash
# С Python инструментом
python -m gpt_oss.chat --backend metal --python models/gpt-oss-20b/metal/model.bin

# С браузерным инструментом
python -m gpt_oss.chat --backend metal --browser models/gpt-oss-20b/metal/model.bin
```

## Модели

### gpt-oss-20b
- **Размер**: ~21B параметров (3.6B активных)
- **Память**: ~16GB
- **Рекомендуется для**: M3 Pro, локальное использование

### gpt-oss-120b
- **Размер**: ~117B параметров (5.1B активных)
- **Память**: ~80GB
- **Рекомендуется для**: Серверы с мощными GPU

## Особенности

### Metal бэкенд
- Оптимизирован для Apple Silicon
- Использует Metal Performance Shaders
- Поддерживает MXFP4 квантизацию

### Harmony формат
- Новый формат чата от OpenAI
- Поддерживает reasoning effort
- Полный chain-of-thought

### Инструменты
- **Python**: Выполнение Python кода
- **Browser**: Веб-серфинг
- **Apply Patch**: Применение патчей

## Устранение неполадок

### Ошибка импорта
```bash
# Переустановите gpt-oss
cd gpt-oss
uv pip install -e ".[metal]" --force-reinstall
```

### Нехватка памяти
- Используйте gpt-oss-20b вместо gpt-oss-120b
- Закройте другие приложения
- Увеличьте swap память

### Медленная работа
- Убедитесь, что используется Metal бэкенд
- Проверьте температуру системы
- Используйте reasoning effort "low" для быстрых ответов

## Полезные команды

### Информация о системе
```bash
# Версия Python
python --version

# Версия PyTorch
python -c "import torch; print(torch.__version__)"

# Поддержка Metal
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Мониторинг ресурсов
```bash
# Использование памяти
top -l 1 | grep "PhysMem"

# Использование GPU
system_profiler SPDisplaysDataType
```

## Ссылки
- [Официальный репозиторий gpt-oss](https://github.com/openai/gpt-oss)
- [Документация Harmony](https://cookbook.openai.com/articles/openai-harmony)
- [Руководство по Metal](https://cookbook.openai.com/articles/gpt-oss/run-metal)
EOF

log_success "README создан: GPT_OSS_README.md"

# Запуск теста
log_info "Запуск теста установки..."
python test_gpt_oss.py

# Финальные инструкции
echo ""
echo "🎉 Установка gpt-oss завершена успешно!"
echo "========================================"
echo ""
echo "📋 Следующие шаги:"
echo "1. Активируйте окружение: source activate_gpt_oss.sh"
echo "2. Загрузите модель: ./download_gpt_oss_model.sh"
echo "3. Запустите тест: python test_gpt_oss.py"
echo ""
echo "📖 Документация: GPT_OSS_README.md"
echo ""
echo "🚀 Примеры использования:"
echo "   # Терминальный чат"
echo "   source activate_gpt_oss.sh"
echo "   python -m gpt_oss.chat --backend metal models/gpt-oss-20b/metal/model.bin"
echo ""
echo "   # Простая генерация"
echo "   python gpt-oss/gpt_oss/metal/examples/generate.py models/gpt-oss-20b/metal/model.bin -p 'Привет!'"
echo ""

log_success "Установка завершена!"




