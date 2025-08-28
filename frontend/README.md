# LLM Gateway Frontend

Современный веб-интерфейс для LLM Gateway системы.

## Возможности

- 💬 **Чат с AI** - интерактивный интерфейс для общения с LLM
- 🤖 **Выбор модели** - переключение между доступными моделями
- 📊 **Мониторинг** - статус всех сервисов системы
- ⚙️ **Настройки** - панель управления системой
- 📱 **Адаптивный дизайн** - работает на всех устройствах

## Технологии

- **React 18** - современный UI фреймворк
- **Tailwind CSS** - утилитарный CSS фреймворк
- **Lucide React** - красивые иконки
- **Axios** - HTTP клиент
- **Nginx** - веб-сервер для production

## Разработка

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm start

# Сборка для production
npm run build
```

## Переменные окружения

```bash
REACT_APP_API_BASE=http://localhost:8080
REACT_APP_API_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmcm9udGVuZC11c2VyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZnJvbnRlbmQtdXNlciIsImV4cCI6OTk5OTk5OTk5OX0uZnJvbnRlbmQtc2lnbmF0dXJl
```

## Docker

```bash
# Сборка образа
docker build -t llm-gateway-frontend .

# Запуск контейнера
docker run -p 80:80 llm-gateway-frontend
```
