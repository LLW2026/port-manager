#!/bin/bash

echo "=========================================="
echo "  端口管理工具 - 启动脚本"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查并安装依赖
echo "检查依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动服务
echo "启动服务..."
python3 main.py
