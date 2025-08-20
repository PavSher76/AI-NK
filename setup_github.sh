#!/bin/bash

# AI-НК - Скрипт настройки GitHub репозитория

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Git
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git не установлен. Установите Git и попробуйте снова."
        exit 1
    fi
    print_success "Git найден"
}

# Проверка наличия GitHub CLI
check_gh() {
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI не установлен. Установите GitHub CLI для автоматического создания репозитория."
        print_info "Установка GitHub CLI: https://cli.github.com/"
        return 1
    fi
    print_success "GitHub CLI найден"
    return 0
}

# Инициализация Git репозитория
init_git() {
    print_info "Инициализация Git репозитория..."
    
    # Инициализация Git
    git init
    
    # Добавление всех файлов
    git add .
    
    # Первый коммит
    git commit -m "feat: первичная инициализация проекта AI-НК

- Добавлена полная система нормоконтроля
- AI-чат с загрузкой файлов
- Автоматическая проверка документов
- Мониторинг и аналитика
- Безопасная аутентификация
- Документация и руководства"
    
    print_success "Git репозиторий инициализирован"
}

# Создание репозитория на GitHub (если доступен GitHub CLI)
create_github_repo() {
    if check_gh; then
        print_info "Создание репозитория на GitHub..."
        
        # Проверка авторизации в GitHub
        if ! gh auth status &> /dev/null; then
            print_warning "Не авторизован в GitHub CLI. Выполните 'gh auth login'"
            return 1
        fi
        
        # Создание репозитория
        gh repo create ai-nk \
            --public \
            --description "AI-НК - Интеллектуальная система автоматизированного нормоконтроля документов" \
            --homepage "https://github.com/your-username/ai-nk" \
            --topic "ai,norm-control,document-processing,fastapi,react,postgresql" \
            --source . \
            --remote origin \
            --push
        
        print_success "Репозиторий создан на GitHub"
        return 0
    else
        print_warning "GitHub CLI недоступен. Создайте репозиторий вручную."
        return 1
    fi
}

# Ручное создание репозитория
manual_github_setup() {
    print_info "Ручная настройка GitHub репозитория..."
    
    echo ""
    echo "📋 Инструкции по созданию репозитория на GitHub:"
    echo ""
    echo "1. Перейдите на https://github.com/new"
    echo "2. Введите имя репозитория: ai-nk"
    echo "3. Добавьте описание: AI-НК - Интеллектуальная система автоматизированного нормоконтроля документов"
    echo "4. Выберите тип: Public"
    echo "5. НЕ инициализируйте с README (у нас уже есть)"
    echo "6. Нажмите 'Create repository'"
    echo ""
    echo "После создания репозитория выполните следующие команды:"
    echo ""
    echo "git remote add origin https://github.com/YOUR_USERNAME/ai-nk.git"
    echo "git branch -M main"
    echo "git push -u origin main"
    echo ""
    
    read -p "Создали ли вы репозиторий на GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Добавление удаленного репозитория..."
        
        # Запрос имени пользователя
        read -p "Введите ваше имя пользователя GitHub: " github_username
        
        # Добавление удаленного репозитория
        git remote add origin "https://github.com/$github_username/ai-nk.git"
        git branch -M main
        git push -u origin main
        
        print_success "Репозиторий подключен к GitHub"
    else
        print_warning "Пропущено подключение к GitHub"
    fi
}

# Настройка GitHub Pages (если репозиторий публичный)
setup_github_pages() {
    print_info "Настройка GitHub Pages..."
    
    # Создание ветки gh-pages
    git checkout -b gh-pages
    
    # Создание простой страницы
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-НК - Система нормоконтроля</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            max-width: 800px;
            padding: 2rem;
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        p {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .feature {
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        .btn {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI-НК</h1>
        <p>Интеллектуальная система автоматизированного нормоконтроля документов</p>
        
        <div class="features">
            <div class="feature">
                <h3>🤖 AI-чат</h3>
                <p>Обработка документов через чат-интерфейс</p>
            </div>
            <div class="feature">
                <h3>📄 Парсинг</h3>
                <p>Поддержка PDF, Word, Excel форматов</p>
            </div>
            <div class="feature">
                <h3>🔍 Нормоконтроль</h3>
                <p>Автоматическая проверка соответствия нормам</p>
            </div>
            <div class="feature">
                <h3>📊 Аналитика</h3>
                <p>Детальная статистика и отчеты</p>
            </div>
        </div>
        
        <div>
            <a href="https://github.com/your-username/ai-nk" class="btn">📦 GitHub</a>
            <a href="https://github.com/your-username/ai-nk/blob/main/INSTALLATION_GUIDE.md" class="btn">📖 Документация</a>
            <a href="https://github.com/your-username/ai-nk/issues" class="btn">🐛 Issues</a>
        </div>
    </div>
</body>
</html>
EOF
    
    # Коммит и пуш
    git add index.html
    git commit -m "docs: добавлена страница GitHub Pages"
    git push origin gh-pages
    
    # Возврат на основную ветку
    git checkout main
    
    print_success "GitHub Pages настроен"
    print_info "Включите GitHub Pages в настройках репозитория (Settings > Pages)"
}

# Создание релиза
create_release() {
    print_info "Создание первого релиза..."
    
    # Создание тега
    git tag -a v1.0.0 -m "🎉 Первый релиз AI-НК v1.0.0

- Полная система нормоконтроля
- AI-чат с загрузкой файлов
- Автоматическая проверка документов
- Мониторинг и аналитика
- Безопасная аутентификация
- Документация и руководства"
    
    # Пуш тега
    git push origin v1.0.0
    
    print_success "Тег v1.0.0 создан"
    
    # Создание релиза через GitHub CLI (если доступен)
    if command -v gh &> /dev/null; then
        gh release create v1.0.0 \
            --title "🎉 AI-НК v1.0.0 - Первый релиз" \
            --notes "## 🎉 Первый релиз системы AI-НК

### ✨ Что нового:
- 🤖 AI-чат с поддержкой загрузки файлов
- 📄 Обработка документов (PDF, Word, Excel)
- 🔍 Автоматический нормоконтроль
- 📊 Детальная аналитика и отчеты
- 🔐 Безопасная аутентификация
- 📱 Современный интерфейс
- 📈 Мониторинг системы

### 🚀 Быстрый старт:
1. Клонируйте репозиторий
2. Запустите \`./install.sh\`
3. Откройте https://localhost

### 📚 Документация:
- [Руководство по установке](INSTALLATION_GUIDE.md)
- [API документация](docs/api.md)
- [Руководство пользователя](docs/user-guide.md)

### 🔧 Технологии:
- Frontend: React.js + Tailwind CSS
- Backend: FastAPI (Python)
- База данных: PostgreSQL + pgvector
- LLM: Ollama (Llama2)
- Аутентификация: Keycloak
- Контейнеризация: Docker" \
            --latest
        
        print_success "Релиз создан на GitHub"
    else
        print_info "Создайте релиз вручную на GitHub: https://github.com/your-username/ai-nk/releases"
    fi
}

# Основная функция
main() {
    echo "=========================================="
    echo "    AI-НК - Настройка GitHub репозитория"
    echo "=========================================="
    echo ""
    
    # Проверки
    check_git
    
    # Инициализация Git
    init_git
    
    # Создание репозитория на GitHub
    if ! create_github_repo; then
        manual_github_setup
    fi
    
    # Настройка GitHub Pages
    read -p "Настроить GitHub Pages? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_github_pages
    fi
    
    # Создание релиза
    read -p "Создать первый релиз v1.0.0? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_release
    fi
    
    echo ""
    echo "=========================================="
    print_success "Настройка GitHub репозитория завершена!"
    echo "=========================================="
    echo ""
    echo "🌐 Репозиторий: https://github.com/your-username/ai-nk"
    echo "📖 Документация: https://github.com/your-username/ai-nk/blob/main/README.md"
    echo "🐛 Issues: https://github.com/your-username/ai-nk/issues"
    echo "📦 Releases: https://github.com/your-username/ai-nk/releases"
    echo ""
    print_info "Не забудьте обновить ссылки в документации!"
}

# Запуск основной функции
main "$@"
