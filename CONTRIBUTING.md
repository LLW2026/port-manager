# 贡献指南

感谢你对 Port Manager 项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告问题

1. 使用 [GitHub Issues](https://github.com/your-username/port-manager/issues) 报告问题
2. 描述问题的详细信息
3. 提供复现步骤
4. 附上错误日志（如有）

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/your-username/port-manager.git
cd port-manager

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

### 代码规范

- 使用 Python 3.8+ 语法
- 遵循 PEP 8 代码规范
- 添加必要的注释
- 更新相关文档

### 提交规范

提交信息格式：
```
<type>: <description>

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat: 添加端口批量分配功能

- 支持一次分配多个端口
- 添加端口范围选择

Closes #123
```

## 功能建议

欢迎在 Issues 中提出功能建议，请描述：
1. 功能的使用场景
2. 期望的实现方式
3. 是否愿意参与开发

## 问题解答

如有问题，可通过以下方式联系：
- GitHub Issues
- Discussion 讨论区

## 许可证

贡献的代码将基于 MIT 许可证开源。