#!/bin/bash

# AI-НК - Очистка истории Git от крупных файлов
# ВНИМАНИЕ: Этот скрипт переписывает историю Git!

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Проверка, что мы в Git репозитории
if [ ! -d ".git" ]; then
    log_error "Не найден Git репозиторий. Запустите скрипт из корня проекта."
    exit 1
fi

# Предупреждение
echo "⚠️  ВНИМАНИЕ: Этот скрипт переписывает историю Git!"
echo "📋 Что будет сделано:"
echo "   1. Удаление крупных файлов из истории"
echo "   2. Очистка кэша Git"
echo "   3. Сжатие репозитория"
echo "   4. Принудительный push (если указан --force-push)"
echo ""
echo "🔴 ЭТО НЕОБРАТИМАЯ ОПЕРАЦИЯ!"
echo ""

read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Операция отменена."
    exit 0
fi

# Создание резервной копии
log_info "Создание резервной копии..."
BACKUP_DIR="git-backup-$(date +%Y%m%d_%H%M%S)"
cp -r .git "$BACKUP_DIR"
log_success "Резервная копия создана: $BACKUP_DIR"

# Размер репозитория до очистки
SIZE_BEFORE=$(du -sh .git | cut -f1)
log_info "Размер репозитория до очистки: $SIZE_BEFORE"

# Список файлов для удаления из истории
FILES_TO_REMOVE=(
    "*.tar.gz"
    "*.zip"
    "*.rar"
    "*.7z"
    "venv/"
    "env/"
    ".venv/"
    "calc_env/"
    "gpt_oss_env/"
    "local_rag_env/"
    "training_env/"
    "test_env/"
    "node_modules/"
    "models/"
    "*.log"
    "logs/"
    "*.pdf"
    "*.docx"
    "*.csv"
    "*.json"
    "*.pkl"
    "*.model"
    "*.h5"
    "*.pb"
    "*.onnx"
    "uploads/"
    "data/"
    "backups/"
    "ssl/"
    "*.pem"
    "*.key"
    "*.crt"
    "gpt-oss/"
    "test_*/"
    "TestDocs/"
    "unique_test*"
    "final_*.pdf"
    "report_*.pdf"
    "ai-nk-deployment/packages/"
)

# Удаление файлов из истории Git
log_info "Удаление крупных файлов из истории Git..."

for pattern in "${FILES_TO_REMOVE[@]}"; do
    log_info "Удаление: $pattern"
    git filter-branch --force --index-filter \
        "git rm -rf --cached --ignore-unmatch '$pattern'" \
        --prune-empty --tag-name-filter cat -- --all 2>/dev/null || true
done

# Очистка ссылок
log_info "Очистка ссылок..."
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

# Очистка кэша
log_info "Очистка кэша Git..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Принудительная очистка
log_info "Принудительная очистка..."
git repack -Ad
git prune

# Размер репозитория после очистки
SIZE_AFTER=$(du -sh .git | cut -f1)
log_success "Размер репозитория после очистки: $SIZE_AFTER"

# Проверка, нужно ли принудительно пушить
if [ "$1" = "--force-push" ]; then
    log_warning "Принудительный push в удаленный репозиторий..."
    git push --force --all
    git push --force --tags
    log_success "Принудительный push завершен"
else
    log_info "Для применения изменений в удаленном репозитории выполните:"
    echo "  git push --force --all"
    echo "  git push --force --tags"
fi

# Создание отчета
REPORT_FILE="git-cleanup-report-$(date +%Y%m%d_%H%M%S).txt"
cat > "$REPORT_FILE" << EOF
AI-НК - Отчет об очистке Git репозитория
========================================

Дата: $(date)
Размер до очистки: $SIZE_BEFORE
Размер после очистки: $SIZE_AFTER
Резервная копия: $BACKUP_DIR

Удаленные файлы и паттерны:
$(printf '%s\n' "${FILES_TO_REMOVE[@]}")

Команды для применения изменений:
git push --force --all
git push --force --tags

ВНИМАНИЕ: Все участники команды должны переклонировать репозиторий!
EOF

log_success "Отчет создан: $REPORT_FILE"

echo ""
log_success "Очистка завершена!"
echo ""
log_warning "ВАЖНО:"
echo "1. Все участники команды должны переклонировать репозиторий"
echo "2. Резервная копия сохранена в: $BACKUP_DIR"
echo "3. Отчет сохранен в: $REPORT_FILE"
echo ""
log_info "Для применения изменений в удаленном репозитории:"
echo "  git push --force --all"
echo "  git push --force --tags"
