# Makefile для тестирования AI-NK

.PHONY: help test test-all test-chat test-outgoing test-ntd test-calculations setup clean reports

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)AI-NK Testing Suite$(NC)"
	@echo "======================"
	@echo ""
	@echo "Доступные команды:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Настроить окружение для тестирования
	@echo "$(GREEN)Настройка окружения для тестирования...$(NC)"
	@if [ ! -d "test_env" ]; then \
		echo "Создание виртуального окружения..."; \
		python3 -m venv test_env; \
	fi
	@echo "Активация виртуального окружения..."
	@. test_env/bin/activate && pip install aiohttp
	@echo "Создание необходимых папок..."
	@mkdir -p reports logs
	@echo "$(GREEN)✅ Окружение настроено$(NC)"

test: setup ## Запустить все тесты
	@echo "$(GREEN)Запуск всех тестов...$(NC)"
	@. test_env/bin/activate && python scripts/run_comprehensive_tests.py

test-all: test ## Алиас для запуска всех тестов

test-chat: setup ## Запустить тесты модуля "Чат с ИИ"
	@echo "$(GREEN)Запуск тестов модуля 'Чат с ИИ'...$(NC)"
	@. test_env/bin/activate && python scripts/test_chat_ai_module.py

test-outgoing: setup ## Запустить тесты модуля "Выходной контроль"
	@echo "$(GREEN)Запуск тестов модуля 'Выходной контроль'...$(NC)"
	@. test_env/bin/activate && python scripts/test_outgoing_control_module.py

test-ntd: setup ## Запустить тесты модуля "Консультация НТД"
	@echo "$(GREEN)Запуск тестов модуля 'Консультация НТД'...$(NC)"
	@. test_env/bin/activate && python scripts/test_ntd_consultation_module.py

test-calculations: setup ## Запустить тесты модуля "Расчеты"
	@echo "$(GREEN)Запуск тестов модуля 'Расчеты'...$(NC)"
	@. test_env/bin/activate && python scripts/test_calculations_module.py

reports: ## Показать отчеты
	@echo "$(GREEN)Отчеты тестирования:$(NC)"
	@echo "======================"
	@if [ -f "reports/comprehensive_test_report.html" ]; then \
		echo "  📄 HTML отчет: reports/comprehensive_test_report.html"; \
	fi
	@if [ -f "reports/comprehensive_test_report.json" ]; then \
		echo "  📊 JSON отчет: reports/comprehensive_test_report.json"; \
	fi
	@if [ -f "reports/comprehensive_test_report.txt" ]; then \
		echo "  📋 Текстовый отчет: reports/comprehensive_test_report.txt"; \
	fi
	@if [ -f "logs/comprehensive_test_suite.log" ]; then \
		echo "  📝 Логи: logs/comprehensive_test_suite.log"; \
	fi

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	@rm -rf __pycache__ *.pyc
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

clean-all: clean ## Очистить все (включая виртуальное окружение)
	@echo "$(YELLOW)Полная очистка...$(NC)"
	@rm -rf test_env
	@rm -rf reports/*.json reports/*.html reports/*.txt
	@rm -rf logs/*.log
	@echo "$(GREEN)✅ Полная очистка завершена$(NC)"

status: ## Показать статус сервисов
	@echo "$(GREEN)Статус сервисов AI-NK:$(NC)"
	@echo "========================"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ai-nk || echo "Сервисы не запущены"

check-services: ## Проверить доступность сервисов
	@echo "$(GREEN)Проверка доступности сервисов...$(NC)"
	@echo "====================================="
	@for port in 8001 8002 8003 8004 8005 8006 8007 8443 443; do \
		if nc -z localhost $$port 2>/dev/null; then \
			echo "  ✅ Порт $$port доступен"; \
		else \
			echo "  ❌ Порт $$port недоступен"; \
		fi; \
	done

install-deps: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	@. test_env/bin/activate && pip install --upgrade pip
	@. test_env/bin/activate && pip install aiohttp

# По умолчанию показывать справку
.DEFAULT_GOAL := help
