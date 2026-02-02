# 🤝 贡献指南

感谢你考虑为 AI Daily Collector 贡献代码！本指南将帮助你开始。

## 🎯 我们需要什么？

- 🐛 **Bug 修复**: 发现并修复问题
- ✨ **新功能**: 添加新功能或改进现有功能
- 📚 **文档**: 改进文档或添加翻译
- 🎨 **体验优化**: 改进用户界面或工作流

## 🚀 开始贡献

### 1. Fork 项目

点击 GitHub 页面右上角的 Fork 按钮。

### 2. 克隆你的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/ai-daily-collector.git
cd ai-daily-collector
```

### 3. 创建分支

```bash
git checkout -b feature/amazing-feature
# 或
git checkout -b fix/annoying-bug
```

### 4. 安装开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov black flake8
```

### 5. 进行更改

确保你的代码：
- 遵循 PEP 8 风格指南
- 添加适当的注释
- 包含测试用例（如果适用）

### 6. 测试

```bash
# 运行所有测试
pytest

# 检查代码风格
flake8 .
black --check .
```

### 7. 提交

```bash
git add .
git commit -m "Add: 简要描述你的更改"
```

### 8. 推送并创建 PR

```bash
git push origin feature/amazing-feature
```

然后在 GitHub 上创建 Pull Request。

## 📋 代码规范

### Python 风格

- 使用 Python 3.10+ 语法
- 函数/方法需要类型注解
- 使用 `black` 自动格式化
- 使用 `flake8` 检查代码质量

### 提交信息格式

```
<类型>: <描述>

[可选的正文]

[可选的脚注]
```

类型包括：
- `Add`: 新功能
- `Fix`: Bug 修复
- `Update`: 更新现有功能
- `Refactor`: 代码重构
- `Docs`: 文档改进
- `Style`: 代码格式调整
- `Test`: 测试相关

### 示例

```
Add: 支持新的 RSS 源配置格式

- 添加 YAML 配置文件解析
- 支持按优先级排序 RSS 源
- 修复了字符编码问题

Closes #123
```

## 🐛 报告问题

当报告问题时，请包含：

1. **问题描述**: 清晰描述问题
2. **复现步骤**: 一步步说明如何复现
3. **期望行为**: 你期望发生什么
4. **实际行为**: 实际发生了什么
5. **日志**: 相关错误日志
6. **环境**: Python 版本、操作系统等

## 💬 获取帮助

- 📧 邮件: 你的邮箱
- 💬 讨论: GitHub Discussions
- 🐛 问题: GitHub Issues

## 📜 行为准则

请尊重他人，遵守我们的[行为准则](CODE_OF_CONDUCT.md)。

感谢你的贡献！ 🎉
