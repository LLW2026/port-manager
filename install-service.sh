#!/bin/bash

echo "=========================================="
echo "  Port Manager - 安装 systemd 服务"
echo "=========================================="

# 获取Python包路径
PYTHON_PATH=$(python3 -c "import site; print(site.getusersitepackages())")
echo "Python包路径: $PYTHON_PATH"

# 创建服务文件
echo "[1/5] 创建服务文件..."
sudo tee /etc/systemd/system/port-manager.service > /dev/null << EOF
[Unit]
Description=Port Manager - 端口管理工具
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/zvol/n004/home-new/liuwu/port-manager
ExecStart=/usr/bin/python3 /zvol/n004/home-new/liuwu/port-manager/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$PYTHON_PATH

[Install]
WantedBy=multi-user.target
EOF
echo "      服务文件已创建"

# 重载systemd配置
echo "[2/5] 重载 systemd 配置..."
sudo systemctl daemon-reload
echo "      完成"

# 停掉当前运行的进程和失败的服务
echo "[3/5] 停止当前进程..."
sudo systemctl stop port-manager 2>/dev/null
pkill -f "python3.*main.py" 2>/dev/null
sleep 1
echo "      完成"

# 启动服务
echo "[4/5] 启动服务..."
sudo systemctl start port-manager
echo "      完成"

# 设置开机自启
echo "[5/5] 设置开机自启..."
sudo systemctl enable port-manager 2>/dev/null
echo "      完成"

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "常用命令："
echo "  查看状态: sudo systemctl status port-manager"
echo "  停止服务: sudo systemctl stop port-manager"
echo "  重启服务: sudo systemctl restart port-manager"
echo "  查看日志: sudo journalctl -u port-manager -f"
echo ""

# 等待服务启动
sleep 3

# 显示服务状态
echo "当前服务状态："
sudo systemctl status port-manager --no-pager
