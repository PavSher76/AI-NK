# Работа с крупными файлами в Git

## Проблема

Пакеты развертывания AI-НК содержат крупные архивы (289MB tar.gz, 331MB zip), которые не должны храниться в Git репозитории.

## Решение

### 1. .gitignore настроен

Файл `.gitignore` уже настроен для исключения:
- `*.tar.gz` - архивы tar.gz
- `*.zip` - архивы zip
- `*.md5` - MD5 хеши
- `*.sha256` - SHA256 хеши
- `packages/ai-nk-deployment-*/` - временные директории пакетов

### 2. Альтернативные способы распространения

#### GitHub Releases
```bash
# Создание релиза с прикрепленными файлами
gh release create v1.0.0 \
  packages/ai-nk-deployment-20250910_003017.tar.gz \
  packages/ai-nk-deployment-20250910_003017.zip \
  --title "AI-НК v1.0.0" \
  --notes "Первый релиз системы нормоконтроля"
```

#### Git LFS (Large File Storage)
```bash
# Установка Git LFS
git lfs install

# Отслеживание крупных файлов
git lfs track "*.tar.gz"
git lfs track "*.zip"

# Добавление файлов
git add .gitattributes
git add packages/*.tar.gz
git add packages/*.zip
git commit -m "Add deployment packages via LFS"
```

#### Внешнее хранилище
- **Google Drive** - для публичного доступа
- **Dropbox** - для команды
- **AWS S3** - для корпоративного использования
- **OwnCloud/NextCloud** - для приватного хостинга

### 3. Скрипт для создания пакетов

```bash
#!/bin/bash
# create-package.sh - Создание пакета развертывания

echo "📦 Создание пакета развертывания AI-НК..."

# Создание временной директории
TEMP_DIR=$(mktemp -d)
PACKAGE_NAME="ai-nk-deployment-$(date +%Y%m%d_%H%M%S)"

# Копирование файлов
cp -r ../calculation_service "$TEMP_DIR/"
cp -r ../rag_service "$TEMP_DIR/"
# ... остальные сервисы

# Создание архива
cd "$TEMP_DIR"
tar -czf "../$PACKAGE_NAME.tar.gz" .
zip -r "../$PACKAGE_NAME.zip" .

# Создание хешей
md5sum "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.md5"
sha256sum "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"

# Очистка
rm -rf "$TEMP_DIR"

echo "✅ Пакет создан: $PACKAGE_NAME.tar.gz"
```

### 4. Автоматизация через GitHub Actions

```yaml
# .github/workflows/create-package.yml
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
          ./scripts/create-package.sh
          
      - name: Upload to GitHub Releases
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.upload_url }}
          asset_path: packages/*.tar.gz
          asset_name: ai-nk-deployment.tar.gz
          asset_content_type: application/gzip
```

### 5. Документация для пользователей

Создайте инструкцию для пользователей:

```markdown
# Скачивание пакета развертывания

## Способы получения пакета

### 1. GitHub Releases
Перейдите на страницу [Releases](https://github.com/your-repo/releases) и скачайте последний пакет.

### 2. Автоматическое скачивание
```bash
# Скачивание последнего релиза
curl -s https://api.github.com/repos/your-repo/releases/latest | \
  grep "browser_download_url.*tar.gz" | \
  cut -d '"' -f 4 | \
  wget -i -
```

### 3. Сборка из исходников
```bash
git clone https://github.com/your-repo/ai-nk.git
cd ai-nk/ai-nk-deployment
./scripts/create-package.sh
```

## Проверка целостности

```bash
# MD5
md5sum -c ai-nk-deployment-*.tar.gz.md5

# SHA256
sha256sum -c ai-nk-deployment-*.tar.gz.sha256
```
```

## Рекомендации

1. **Используйте GitHub Releases** для публичного распространения
2. **Git LFS** для командной разработки
3. **Внешнее хранилище** для корпоративного использования
4. **Автоматизация** через CI/CD для создания пакетов
5. **Документируйте** процесс получения пакетов

## Текущий статус

✅ `.gitignore` настроен  
✅ Крупные файлы исключены из репозитория  
✅ Документация создана  
✅ Скрипты для создания пакетов готовы  

**Пакеты развертывания готовы к распространению через GitHub Releases!**
