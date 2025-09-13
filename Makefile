# AI-NK Makefile
# ==============

.PHONY: help build start stop restart status logs clean deploy quick-deploy

# Переменные
COMPOSE_FILE = docker-compose.production.yml
IMAGE_NAME = ai-nk
TAG = latest

# Цвета для вывода
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)AI-NK Management Commands$(NC)"
	@echo "=========================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make deploy        # Полное развертывание"
	@echo "  make quick-deploy  # Быстрое развертывание"
	@echo "  make logs          # Просмотр логов"
	@echo "  make clean         # Очистка системы"

build: ## Собрать Docker образ
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -f Dockerfile.production -t $(IMAGE_NAME):$(TAG) .
	@echo "$(GREEN)✅ Image built successfully$(NC)"

start: ## Запустить систему
	@echo "$(BLUE)Starting AI-NK system...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ System started$(NC)"

stop: ## Остановить систему
	@echo "$(BLUE)Stopping AI-NK system...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ System stopped$(NC)"

restart: ## Перезапустить систему
	@echo "$(BLUE)Restarting AI-NK system...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	sleep 5
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ System restarted$(NC)"

status: ## Показать статус системы
	@echo "$(BLUE)System Status:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(BLUE)Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

logs: ## Показать логи всех сервисов
	@echo "$(BLUE)Showing logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-ai-nk: ## Показать логи основного сервиса
	@echo "$(BLUE)Showing AI-NK logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f ai-nk

logs-db: ## Показать логи базы данных
	@echo "$(BLUE)Showing database logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f norms-db

logs-redis: ## Показать логи Redis
	@echo "$(BLUE)Showing Redis logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f redis

logs-qdrant: ## Показать логи Qdrant
	@echo "$(BLUE)Showing Qdrant logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f qdrant

clean: ## Очистить систему (удалить контейнеры и volumes)
	@echo "$(YELLOW)⚠️  This will remove all containers and volumes!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "$(BLUE)Cleaning system...$(NC)"; \
		docker-compose -f $(COMPOSE_FILE) down -v; \
		docker system prune -f; \
		echo "$(GREEN)✅ System cleaned$(NC)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

deploy: build start ## Полное развертывание (сборка + запуск)
	@echo "$(GREEN)✅ Deployment completed$(NC)"
	@echo ""
	@echo "$(BLUE)System URLs:$(NC)"
	@echo "  Web Interface: http://localhost"
	@echo "  HTTPS:         https://localhost"
	@echo "  API Gateway:   https://localhost:8443"
	@echo ""
	@echo "$(BLUE)Management:$(NC)"
	@echo "  Status: make status"
	@echo "  Logs:   make logs"
	@echo "  Stop:   make stop"

quick-deploy: ## Быстрое развертывание (использует скрипт)
	@echo "$(BLUE)Quick deployment...$(NC)"
	@chmod +x quick-deploy.sh
	@./quick-deploy.sh

health: ## Проверить состояние системы
	@echo "$(BLUE)Health Check:$(NC)"
	@echo -n "Web Interface: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "❌"
	@echo ""
	@echo -n "API Gateway: "
	@curl -s -o /dev/null -w "%{http_code}" https://localhost:8443/health || echo "❌"
	@echo ""
	@echo -n "Document Parser: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "❌"
	@echo ""
	@echo -n "RAG Service: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health || echo "❌"

backup: ## Создать резервную копию данных
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups
	@docker-compose -f $(COMPOSE_FILE) exec -T norms-db pg_dump -U norms_user norms_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup created in backups/ directory$(NC)"

restore: ## Восстановить из резервной копии (требует BACKUP_FILE)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)❌ Please specify BACKUP_FILE=path/to/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring from $(BACKUP_FILE)...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec -T norms-db psql -U norms_user norms_db < $(BACKUP_FILE)
	@echo "$(GREEN)✅ Restore completed$(NC)"

update: ## Обновить систему (pull + rebuild + restart)
	@echo "$(BLUE)Updating system...$(NC)"
	@git pull origin main
	@make build
	@make restart
	@echo "$(GREEN)✅ System updated$(NC)"

shell: ## Подключиться к контейнеру AI-NK
	@echo "$(BLUE)Connecting to AI-NK container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec ai-nk /bin/bash

db-shell: ## Подключиться к базе данных
	@echo "$(BLUE)Connecting to database...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec norms-db psql -U norms_user -d norms_db

monitor: ## Мониторинг ресурсов в реальном времени
	@echo "$(BLUE)Resource monitoring (Ctrl+C to exit)...$(NC)"
	@watch -n 2 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"'

# Установка прав доступа
install:
	@echo "$(BLUE)Setting up permissions...$(NC)"
	@chmod +x build-and-deploy.sh quick-deploy.sh scripts/start.sh scripts/init.sh
	@echo "$(GREEN)✅ Permissions set$(NC)"

# Проверка зависимостей
check-deps:
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker is not installed$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)❌ Docker Compose is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✅ All dependencies are installed$(NC)"

# Показать информацию о системе
info:
	@echo "$(BLUE)AI-NK System Information$(NC)"
	@echo "=========================="
	@echo ""
	@echo "$(YELLOW)System URLs:$(NC)"
	@echo "  Web Interface: http://localhost"
	@echo "  HTTPS:         https://localhost"
	@echo "  API Gateway:   https://localhost:8443"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  Document Parser: http://localhost:8001"
	@echo "  Rule Engine:     http://localhost:8002"
	@echo "  RAG Service:     http://localhost:8003"
	@echo "  Calculation:     http://localhost:8004"
	@echo "  VLLM Service:    http://localhost:8005"
	@echo "  Outgoing Control: http://localhost:8006"
	@echo "  Spellchecker:    http://localhost:8007"
	@echo ""
	@echo "$(YELLOW)Database & Cache:$(NC)"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Qdrant:     http://localhost:6333"
	@echo "  Redis:      localhost:6379"
	@echo ""
	@echo "$(YELLOW)Management Commands:$(NC)"
	@echo "  make status    - Show system status"
	@echo "  make logs      - Show logs"
	@echo "  make stop      - Stop system"
	@echo "  make restart   - Restart system"
	@echo "  make clean     - Clean system"
