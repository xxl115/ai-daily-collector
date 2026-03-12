# 重构计划：渐进迁移

## 目标
将 worker.py (1539 行) 拆分为模块化结构

## 步骤

### Step 1: 提取 API 路由 ✅ (已完成)
- 创建 `api/handlers.py`
- 创建 `api/mcp_tools.py`

### Step 2: 提取 Storage 适配器
- 将 `WorkersD1StorageAdapter` 移到 `api/storage.py`
- 减少 worker.py 中的代码量

### Step 3: 提取分类逻辑
- 将 `classify()` 函数移到 `api/classifier.py`
- 独立模块便于测试

### Step 4: 简化 worker.py
- 只保留入口和路由组装
- 导入和使用新模块

## 验证
每次完成后运行测试确保功能正常
