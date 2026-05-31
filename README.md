# 🔌 Port Manager - 多主机端口管理工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

> 轻量级的多主机端口管理工具，统一管理服务器端口分配，支持AI集成。

[English](#english) | [中文](#中文)

---

## ✨ 功能特性

### 核心功能
- 🖥️ **多主机管理** - 通过SSH统一管理多台服务器
- 🔌 **端口分配** - 自动/手动分配端口给项目
- 📊 **项目关联** - 端口与项目绑定，项目删除自动回收
- 🏊 **端口池** - 可配置的端口范围管理
- 📝 **分配历史** - 完整的端口分配记录
- 🔍 **冲突检测** - 自动检测端口占用

### 界面功能
- 📱 **响应式Web界面** - 类云控制台风格
- 🔎 **搜索筛选** - 按端口、项目、状态搜索
- 📦 **项目分组** - 按项目分组展示端口
- 🌐 **Web标记** - 标记Web服务并快速访问
- 📈 **统计面板** - 端口使用情况统计

### AI集成
- 🤖 **Claude Skill** - 通过AI助手管理端口
- 💬 **自然语言** - "为项目xxx分配端口"
- 🔄 **自动检测** - 自动识别当前主机

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/port-manager.git
cd port-manager

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 访问

启动后访问：
- 本机：http://localhost:35765
- 局域网：http://<你的IP>:35765
- API文档：http://<你的IP>:35765/docs

### systemd 部署（推荐）

```bash
# 运行安装脚本
./install-service.sh

# 常用命令
sudo systemctl status port-manager
sudo systemctl restart port-manager
sudo journalctl -u port-manager -f
```

---

## 📖 使用说明

### 添加主机

1. 点击右上角「🖥️ 主机管理」
2. 点击「+ 添加主机」
3. 填写主机信息（名称、IP、SSH端口、用户名、密钥）
4. 测试连接并保存

### 分配端口

**Web界面：**
1. 选择目标主机
2. 点击「+ 添加端口」
3. 填写端口信息

**API调用：**
```bash
# 创建项目并自动分配端口
curl -X POST http://localhost:35765/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "host_id": 1, "auto_allocate": true, "port_count": 2}'

# 查询可用端口
curl http://localhost:35765/api/allocations/available?host_id=1&count=10
```

**Claude Skill：**
```
/port-allocate    # 为项目分配端口
/port-available   # 查询可用端口
/port-release     # 释放端口
/port-list        # 查看分配列表
```

---

## 🏗️ 技术架构

```
port-manager/
├── main.py              # 主入口
├── database.py          # 端口数据库
├── allocation_db.py     # 分配管理数据库
├── models.py            # 数据模型
├── ssh_manager.py       # SSH连接管理
├── routers/
│   ├── ports.py         # 端口API
│   ├── hosts.py         # 主机API
│   └── allocations.py   # 分配API
├── static/              # 前端资源
├── templates/           # HTML模板
└── install-service.sh   # systemd安装脚本
```

### 技术栈

- **后端**：Python + FastAPI
- **数据库**：SQLite
- **SSH**：Paramiko
- **前端**：原生HTML/CSS/JS

---

## 📚 API 文档

启动服务后访问：http://localhost:35765/docs

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/hosts` | GET/POST | 主机管理 |
| `/api/ports` | GET/POST | 端口管理 |
| `/api/projects` | GET/POST | 项目管理 |
| `/api/allocations` | GET/POST | 端口分配 |
| `/api/allocations/available` | GET | 可用端口 |
| `/api/stats/allocations` | GET | 分配统计 |

---

## 🤖 Claude Skill 集成

### 安装 Skill

将 `commands/` 目录下的文件复制到 `~/.claude/commands/`：

```bash
cp commands/port-*.md ~/.claude/commands/
```

### 使用 Skill

```
/port-allocate    # 为项目分配端口
/port-available   # 查询可用端口
/port-release     # 释放端口
/port-list        # 查看分配列表
```

Skill 会自动检测当前主机IP并映射到对应的host_id。

---

## 🐳 Docker 部署（可选）

```bash
# 构建镜像
docker build -t port-manager .

# 运行容器
docker run -d \
  -p 35765:35765 \
  -v ./data:/app/data \
  -v ~/.ssh:/root/.ssh \
  port-manager
```

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Paramiko](https://www.paramiko.org/) - SSH库
- [psutil](https://github.com/giampaolo/psutil) - 系统监控

---

<a id="english"></a>

## English

### Overview

Port Manager is a lightweight multi-host port management tool that helps you manage port allocation across multiple servers through a unified web interface.

### Features

- **Multi-host Management** - Manage multiple servers via SSH
- **Port Allocation** - Auto/manual port assignment to projects
- **Project Association** - Ports tied to projects, auto-cleanup on deletion
- **Port Pool** - Configurable port range management
- **AI Integration** - Claude Skill for natural language port management

### Quick Start

```bash
git clone https://github.com/your-username/port-manager.git
cd port-manager
pip install -r requirements.txt
python main.py
```

Visit http://localhost:35765

---

**Made with ❤️ by [LLW2026](https://github.com/LLW2026)**