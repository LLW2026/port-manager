# 更新日志

所有重要更改都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，

## [1.0.0] - 2026-05-31

### 新增
- 多主机管理（SSH连接）
- 端口记录CRUD
- 端口状态管理（使用中/空闲/保留）
- 项目管理（创建/删除项目）
- 端口自动分配
- 端口手动分配
- 端口池管理
- 分配历史记录
- 端口冲突检测
- 自动回收（项目删除时释放端口）
- Web服务标记和快速访问
- 按项目分组展示
- 搜索筛选功能
- 统计面板
- Claude Skill集成
- systemd服务安装脚本
- Docker支持

### 技术
- Python + FastAPI后端
- SQLite数据库
- Paramiko SSH库
- 原生HTML/CSS/JS前端

---

## [未发布]

### 计划
- 端口使用率监控
- 批量操作
- 导入/导出功能
- 用户认证
- API Token支持