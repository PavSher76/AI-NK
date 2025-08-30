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
