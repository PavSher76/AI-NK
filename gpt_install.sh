# 1) Клонируем и ставим с Metal-бэкендом
git clone https://github.com/openai/gpt-oss.git
cd gpt-oss
GPTOSS_BUILD_METAL=1 uv pip install -e ".[metal]"

