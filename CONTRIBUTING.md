# 🤝 Руководство по участию в проекте AI-НК

Спасибо за интерес к проекту AI-НК! Мы приветствуем вклад от сообщества.

## 📋 Как внести свой вклад

### 🐛 Сообщение об ошибках

1. Проверьте, не была ли ошибка уже зарегистрирована в [Issues](https://github.com/your-username/ai-nk/issues)
2. Создайте новое issue с подробным описанием:
   - Описание проблемы
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Версия системы и окружение

### 💡 Предложение улучшений

1. Создайте issue с тегом `enhancement`
2. Опишите предлагаемое улучшение
3. Объясните, почему это улучшение полезно
4. Предложите способ реализации

### 🔧 Внесение изменений в код

#### Подготовка окружения

1. **Форкните репозиторий**
   ```bash
   git clone https://github.com/your-username/ai-nk.git
   cd ai-nk
   ```

2. **Создайте ветку для изменений**
   ```bash
   git checkout -b feature/your-feature-name
   # или
   git checkout -b fix/your-bug-fix
   ```

3. **Установите зависимости**
   ```bash
   # Установка системы
   chmod +x install.sh
   ./install.sh
   ```

#### Разработка

1. **Следуйте стандартам кода**:
   - Python: PEP 8
   - JavaScript: ESLint + Prettier
   - Комментарии на русском языке

2. **Тестируйте изменения**:
   ```bash
   # Запуск тестов
   docker-compose exec document-parser python -m pytest
   docker-compose exec rule-engine python -m pytest
   ```

3. **Обновляйте документацию** при необходимости

#### Создание Pull Request

1. **Подготовьте коммиты**:
   ```bash
   git add .
   git commit -m "feat: добавлена новая функция X"
   git push origin feature/your-feature-name
   ```

2. **Создайте Pull Request**:
   - Заполните шаблон PR
   - Опишите изменения
   - Укажите связанные issues
   - Добавьте скриншоты для UI изменений

3. **Дождитесь проверки**:
   - CI/CD проверки
   - Code review
   - Тестирование

## 📝 Стандарты коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Типы коммитов:
- `feat`: новая функция
- `fix`: исправление ошибки
- `docs`: изменения в документации
- `style`: форматирование кода
- `refactor`: рефакторинг кода
- `test`: добавление тестов
- `chore`: обновление зависимостей, конфигурации

### Примеры:
```bash
git commit -m "feat: добавлена поддержка PDF документов"
git commit -m "fix: исправлена ошибка авторизации"
git commit -m "docs: обновлено руководство по установке"
```

## 🏗️ Архитектура проекта

### Структура сервисов:
```
ai-nk/
├── frontend/          # React.js приложение
├── gateway/           # API Gateway (FastAPI)
├── document_parser/   # Парсер документов
├── rule_engine/       # Движок правил
├── rag_service/       # RAG сервис
├── ollama_adapter/    # Адаптер для Ollama
└── configs/           # Конфигурации
```

### Технологический стек:
- **Frontend**: React.js, Tailwind CSS
- **Backend**: FastAPI, Python
- **База данных**: PostgreSQL с pgvector
- **Векторная БД**: Qdrant
- **LLM**: Ollama
- **Аутентификация**: Keycloak
- **Мониторинг**: Prometheus + Grafana

## 🧪 Тестирование

### Запуск тестов:
```bash
# Тесты парсера документов
docker-compose exec document-parser python -m pytest

# Тесты движка правил
docker-compose exec rule-engine python -m pytest

# Тесты RAG сервиса
docker-compose exec rag-service python -m pytest
```

### Покрытие кода:
```bash
# Генерация отчета о покрытии
docker-compose exec document-parser python -m pytest --cov=app --cov-report=html
```

## 📚 Документация

### Обновление документации:
1. Изменения в коде должны сопровождаться обновлением документации
2. Используйте Markdown для документации
3. Добавляйте примеры использования
4. Обновляйте README.md при значительных изменениях

### Структура документации:
- `README.md` - основная документация
- `INSTALLATION_GUIDE.md` - руководство по установке
- `docs/` - дополнительная документация
- Комментарии в коде

## 🔒 Безопасность

### Сообщение об уязвимостях:
1. **НЕ создавайте публичные issues** для уязвимостей
2. Отправьте email на security@ai-nk.local
3. Опишите уязвимость подробно
4. Предложите способ исправления

### Стандарты безопасности:
- Не коммитьте пароли или ключи
- Используйте переменные окружения
- Проверяйте зависимости на уязвимости
- Следуйте принципу наименьших привилегий

## 🏷️ Версионирование

Проект использует [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: несовместимые изменения API
- `MINOR`: новая функциональность (обратно совместимая)
- `PATCH`: исправления ошибок (обратно совместимые)

## 📞 Поддержка

### Получение помощи:
- [Issues](https://github.com/your-username/ai-nk/issues) - для ошибок и предложений
- [Discussions](https://github.com/your-username/ai-nk/discussions) - для вопросов
- Email: support@ai-nk.local

### Сообщество:
- Присоединяйтесь к обсуждениям
- Помогайте другим участникам
- Делитесь опытом использования

## 🎉 Признание вклада

Ваш вклад будет отмечен в:
- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- README.md
- Release notes

Спасибо за участие в развитии AI-НК! 🚀
