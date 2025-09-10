# Руководство по работе с репозиторием AI-НК

## Структура репозитория

```
ai-nk-deployment/
├── .gitignore                 # Исключения для Git
├── README.md                  # Основная документация
├── QUICK_START.md            # Быстрый старт
├── DEPLOYMENT_REPORT.md      # Отчет о развертывании
├── GIT_LARGE_FILES.md        # Работа с крупными файлами
├── REPOSITORY_GUIDE.md       # Это руководство
├── packages/                 # Пакеты развертывания (игнорируются Git)
│   ├── *.tar.gz             # Архивы (игнорируются)
│   ├── *.zip                # Архивы (игнорируются)
│   ├── *.md5                # Хеши (игнорируются)
│   ├── *.sha256             # Хеши (игнорируются)
│   ├── README.md            # Документация пакетов
│   └── PACKAGE_INFO.md      # Информация о пакетах
├── scripts/                  # Скрипты создания пакетов
│   ├── install.sh           # Установка
│   ├── quick-deploy.sh      # Быстрое развертывание
│   └── create-package.sh    # Создание пакетов
├── configs/                  # Шаблоны конфигураций
├── docs/                     # Документация
└── env-templates/            # Шаблоны переменных окружения
```

## Что включено в Git

✅ **Включено:**
- Исходный код всех скриптов
- Документация и README файлы
- Шаблоны конфигураций
- .gitignore файл
- Инструкции по работе

❌ **Исключено:**
- Архивы пакетов (*.tar.gz, *.zip)
- Проверочные суммы (*.md5, *.sha256)
- Временные директории пакетов
- Логи и кэш файлы
- SSL сертификаты
- Файлы с паролями (.env)

## Работа с пакетами развертывания

### Создание пакета

```bash
# Переход в директорию развертывания
cd ai-nk-deployment

# Создание пакета
./scripts/create-package.sh

# Пакет будет создан в packages/
ls packages/
```

### Распространение пакетов

#### 1. GitHub Releases (рекомендуется)

```bash
# Создание тега
git tag v1.0.0
git push origin v1.0.0

# Создание релиза через GitHub CLI
gh release create v1.0.0 \
  packages/ai-nk-deployment-*.tar.gz \
  packages/ai-nk-deployment-*.zip \
  --title "AI-НК v1.0.0" \
  --notes "Первый релиз системы нормоконтроля"
```

#### 2. Внешнее хранилище

```bash
# Загрузка на Google Drive, Dropbox, AWS S3 и т.д.
# Обновление ссылок в документации
```

#### 3. Git LFS (для команды)

```bash
# Установка Git LFS
git lfs install

# Отслеживание крупных файлов
git lfs track "packages/*.tar.gz"
git lfs track "packages/*.zip"

# Добавление файлов
git add .gitattributes
git add packages/*.tar.gz
git add packages/*.zip
git commit -m "Add deployment packages via LFS"
```

## Автоматизация

### GitHub Actions

Создайте `.github/workflows/create-package.yml`:

```yaml
name: Create Deployment Package

on:
  push:
    tags:
      - 'v*'

jobs:
  create-package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create package
        run: |
          cd ai-nk-deployment
          ./scripts/create-package.sh
          
      - name: Upload to GitHub Releases
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.upload_url }}
          asset_path: ai-nk-deployment/packages/*.tar.gz
          asset_name: ai-nk-deployment.tar.gz
          asset_content_type: application/gzip
```

### Локальная автоматизация

```bash
#!/bin/bash
# deploy.sh - Полный цикл развертывания

echo "🚀 AI-НК - Полный цикл развертывания"

# 1. Создание пакета
echo "📦 Создание пакета..."
./scripts/create-package.sh

# 2. Создание тега
echo "🏷️ Создание тега..."
VERSION=$(date +%Y%m%d_%H%M%S)
git tag "v$VERSION"

# 3. Загрузка в GitHub Releases
echo "📤 Загрузка в GitHub Releases..."
gh release create "v$VERSION" \
  packages/ai-nk-deployment-*.tar.gz \
  packages/ai-nk-deployment-*.zip \
  --title "AI-НК v$VERSION" \
  --notes "Автоматический релиз от $(date)"

echo "✅ Развертывание завершено!"
```

## Работа с документацией

### Обновление документации

```bash
# После изменений в пакете
git add README.md DEPLOYMENT_REPORT.md
git commit -m "Update documentation"
git push origin main
```

### Синхронизация с основным репозиторием

```bash
# Получение изменений из основного репозитория
git remote add upstream https://github.com/your-org/ai-nk.git
git fetch upstream
git merge upstream/main

# Обновление пакетов после изменений
./scripts/create-package.sh
```

## Мониторинг репозитория

### Проверка размера

```bash
# Размер репозитория
du -sh .git

# Размер исключенных файлов
du -sh packages/

# Проверка .gitignore
git check-ignore packages/*
```

### Очистка истории

```bash
# Удаление крупных файлов из истории (осторожно!)
git filter-branch --tree-filter 'rm -rf packages/' HEAD

# Принудительная очистка
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Рекомендации

### ✅ Хорошие практики

1. **Всегда используйте .gitignore** для исключения крупных файлов
2. **Создавайте пакеты автоматически** через CI/CD
3. **Документируйте изменения** в каждом релизе
4. **Проверяйте целостность** пакетов перед распространением
5. **Используйте семантическое версионирование** (v1.0.0, v1.1.0, v2.0.0)

### ❌ Чего избегать

1. **Не коммитьте крупные файлы** напрямую в Git
2. **Не храните пароли** в репозитории
3. **Не игнорируйте .gitignore** файл
4. **Не создавайте пакеты вручную** без автоматизации
5. **Не забывайте обновлять документацию**

## Поддержка

- **Документация**: `docs/`
- **Проблемы**: https://github.com/your-repo/issues
- **Обсуждения**: https://github.com/your-repo/discussions

---

**Репозиторий готов к работе с крупными файлами через GitHub Releases!** 🚀
