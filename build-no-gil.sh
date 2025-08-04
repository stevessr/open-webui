#!/bin/bash
set -e

# ==============================================================================
# Open WebUI Nuitka 构建脚本 (无 GIL 版本)
#
# 这个脚本使用 Nuitka 将 Open WebUI 后端编译成一个独立的、无 GIL 的二进制文件。
#
# 前置要求:
# 1. 一个“无 GIL”(nogil) 版本的 Python 3.12+ 必须已安装，并且其可执行文件
#    必须在系统的 PATH 环境变量中。
# 2. 您必须在下方设置 PYTHON_NOGIL_COMMAND 变量，使其与您系统中的命令名一致。
# 3. 前端代码必须已构建，并被复制到项目根目录的 `build` 文件夹中。
#
# ==============================================================================

# --- 配置 ---

# !!! 请务必修改 !!!
# 设置您的无 GIL Python 的命令名。
# 例如，如果您通过 `3.13t -V` 能看到 Python 版本，那么就设置为 "3.13t"。
# 其他可能的例子: "python3.13-nogil", "python-nogil"
PYTHON_NOGIL_COMMAND="3.13t" # <-- 修改此行以匹配您的环境

VENV_DIR=".venv-nogil"
REQUIREMENTS_FILE="backend/requirements.txt"
ENTRY_POINT="backend/open_webui/main.py"
OUTPUT_DIR="dist"
EXECUTABLE_NAME="open_webui_server_nogil"

# --- 步骤 1: 环境准备 ---
echo "--> [1/4] 正在准备无 GIL 构建环境..."

if [ ! -d "$VENV_DIR" ]; then
    echo "正在使用命令 '$PYTHON_NOGIL_COMMAND' 创建虚拟环境..."
    uv venv "$VENV_DIR" --python "$PYTHON_NOGIL_COMMAND"
else
    echo "无 GIL 虚拟环境已存在。"
fi

# 激活虚拟环境 (跨平台)
if [ -f "$VENV_DIR/Scripts/activate" ]; then
  source "$VENV_DIR/Scripts/activate"  # Windows
elif [ -f "$VENV_DIR/bin/activate" ]; then
  source "$VENV_DIR/bin/activate"      # Unix/Linux
else
  echo "错误：找不到虚拟环境的激活脚本。"
  exit 1
fi

echo "正在安装项目依赖和 Nuitka..."
uv pip install -r "$REQUIREMENTS_FILE"
uv pip install -U nuitka ordered-set

echo "环境准备完毕。"
echo ""

# --- 步骤 2: 检查前端文件 ---
echo "--> [2/4] 正在检查前端构建文件..."
if [ ! -d "build" ]; then
    echo "错误：未找到 'build' 目录。"
    echo "请先构建前端: cd src/ && pnpm install && pnpm build && cp -r dist/ ../build/"
    exit 1
else
    echo "前端文件检查通过。"
    echo ""
fi

# --- 步骤 3: 运行 Nuitka 构建 (无 GIL) ---
echo "--> [3/4] 正在启动 Nuitka No-GIL 构建... (这可能需要很长时间)"
CPU_CORES=$(nproc --all || echo 4)

# 使用我们已激活的无 GIL 环境中的 Python 来运行 Nuitka
uv run python -m nuitka \
    --onefile \
    --standalone \
    --python-flag=no_gil \
    --output-dir="$OUTPUT_DIR" \
    --output-filename="$EXECUTABLE_NAME" \
    \
    --jobs="$CPU_CORES" \
    --module-parameter=torch-disable-jit=yes \
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
echo "无 GIL 可执行文件已生成在: $OUTPUT_DIR/$EXECUTABLE_NAME"
echo "你可以通过运行 ./$OUTPUT_DIR/$EXECUTABLE_NAME 来启动服务。"

# 取消激活虚拟环境
deactivate