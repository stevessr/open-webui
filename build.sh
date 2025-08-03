#!/bin/bash
set -e

# ==============================================================================
# Open WebUI Nuitka Builder
#
# 这个脚本使用 Nuitka 将 Open WebUI 后端编译成一个独立的二进制文件。
#
# 前置要求:
# 1. 系统中已安装 Python 3.12+ 和 pip。
# 2. 前端代码已经构建，并且输出目录被复制到了项目根目录下的 `build` 文件夹。
#    例如:
#    cd src/
#    pnpm install && pnpm build
#    cp -r dist/ ../build/
#
# ==============================================================================

# --- 配置 ---
VENV_DIR="nuitka_build_env"
REQUIREMENTS_FILE="backend/requirements.txt"
ENTRY_POINT="backend/open_webui/main.py"
OUTPUT_DIR="dist"
EXECUTABLE_NAME="open_webui_server"

# --- 步骤 1: 环境准备 ---
echo "--> [1/4] 正在准备构建环境..."

if [ ! -d "$VENV_DIR" ]; then
    echo "创建 Python 虚拟环境..."
    uv venv "$VENV_DIR"
else
    echo "虚拟环境已存在。"
fi

# 激活虚拟环境
# 激活虚拟环境 (跨平台)
if [ -f "$VENV_DIR/Scripts/activate" ]; then
  source "$VENV_DIR/Scripts/activate"  # Windows
elif [ -f "$VENV_DIR/bin/activate" ]; then
  source "$VENV_DIR/bin/activate"      # Unix/Linux
else
  echo "错误: 找不到虚拟环境的激活脚本。"
  exit 1
fi

echo "安装项目依赖和 Nuitka..."
uv pip install -r "$REQUIREMENTS_FILE"
uv pip install -U nuitka ordered-set

echo "环境准备完毕。"
echo ""

# --- 步骤 2: 检查前端文件 ---
echo "--> [2/4] 正在检查前端构建文件..."
if [ ! -d "build" ]; then
    echo "错误：未找到 'build' 目录。"
    echo "自动构建前端。"
    pnpm build
else
    echo "前端文件检查通过。"
    echo ""
fi

# --- 步骤 3: 运行 Nuitka 构建 ---
echo "--> [3/4] 正在启动 Nuitka 构建... (这可能需要很长时间)"

uv run python -m nuitka \
    --onefile \
    --standalone \
    --output-dir="$OUTPUT_DIR" \
    --output-filename="$EXECUTABLE_NAME" \
    \
    --enable-plugin=implicit-imports \
    \
    --include-package=open_webui.routers \
    \
    --include-data-dir=backend/open_webui/static=open_webui/static \
    --include-data-dir=backend/open_webui/migrations=open_webui/migrations \
    --include-data-file=backend/open_webui/alembic.ini=alembic.ini \
    --include-data-dir=./build=build \
    \
    "$ENTRY_POINT"

echo ""

# --- 步骤 4: 完成 ---
echo "--> [4/4] 构建完成！"
echo "可执行文件已生成在: $OUTPUT_DIR/$EXECUTABLE_NAME"
echo "你可以通过运行 ./$OUTPUT_DIR/$EXECUTABLE_NAME 来启动服务。"

# 取消激活虚拟环境
deactivate
