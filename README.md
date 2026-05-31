# Port Manager - 端口管理工具

轻量级的端口管理记录工具，用于统一管理多台主机的端口使用情况。

## 功能特性

### 核心功能
- ✅ 端口记录的增删改查
- ✅ 端口状态管理（使用中/空闲/保留）
- ✅ 按端口号、用途、项目搜索筛选
- ✅ 本机端口扫描（自动检测监听端口）
- ✅ SQLite 本地存储
- ✅ Web服务标记和快速访问

### 多主机管理
- ✅ 添加/删除/编辑远程主机
- ✅ SSH连接远程主机
- ✅ 远程端口扫描
- ✅ 统一管理多台主机端口
- ✅ 主机连接状态检测

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 访问 http://<你的IP>:35765
```

## 技术栈

- Python 3.8+
- FastAPI
- SQLite
- Paramiko (SSH连接)
- 原生 HTML/CSS/JS

## 项目结构

```
port-manager/
├── main.py              # 主入口
├── database.py          # 数据库操作
├── models.py            # 数据模型
├── ssh_manager.py       # SSH连接管理
├── requirements.txt     # 依赖
├── routers/
│   ├── ports.py         # 端口相关API
│   └── hosts.py         # 主机相关API
├── static/
│   ├── css/style.css    # 样式
│   └── js/app.js        # 前端逻辑
└── templates/
    └── index.html       # 主页面
```

## API 文档

启动后访问 http://<你的IP>:35765/docs 查看自动生成的 API 文档

## 使用说明

### 添加远程主机
1. 点击右上角「主机管理」按钮
2. 点击「添加主机」
3. 填写主机名称、地址、SSH端口、用户名和密码/密钥
4. 点击「测试连接」验证SSH连接
5. 保存

### 扫描远程端口
1. 在顶部选择目标主机
2. 点击「扫描端口」
3. 系统会通过SSH连接获取该主机的监听端口
4. 未记录的端口可以一键添加

### 管理端口
- 点击「添加端口」手动添加
- 点击 Web 标记切换 Web 服务状态
- 点击「访问」按钮打开 Web 页面
- 按项目分组查看端口
