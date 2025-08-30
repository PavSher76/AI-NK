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
