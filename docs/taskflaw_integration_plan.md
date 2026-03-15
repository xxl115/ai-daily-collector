# TaskFlaw 集成方案

## 目标

利用 TaskFlaw 实现 AI Daily Collector 自动化任务调度

---

## 背景

### 当前状态
- 手动运行脚本采集和处理新闻
- 需要定时触发新闻采集

### 目标状态
- 定时自动采集新闻 (TaskFlaw)
- 自动 LLM 处理 (TaskFlaw DAG)
- 自动生成日报 (TaskFlaw DAG)

---

## 方案设计

### 1. 定时任务 (Cron Jobs)

| 任务名 | 调度 | 说明 |
|--------|------|------|
| 采集新闻 | every 6 hours | 每6小时采集一次 |
| 处理文章 | every 1 hour | 每小时处理待处理文章 |
| 生成日报 | daily at 8am | 每天早上8点生成日报 |

### 2. DAG 工作流

```
新闻采集 → AI分类 → LLM摘要 → 生成日报 → 推送通知
```

#### 节点说明

| 节点 | 功能 | 实现 |
|------|------|------|
| 新闻采集 | 从RSS/API获取新闻 | Python脚本 |
| AI分类 | 判断是否AI相关 | Python脚本 |
| LLM摘要 | 生成摘要/分类/标签 | OpenCode CLI |
| 生成日报 | 生成Markdown | Python脚本 |
| 推送通知 | 推送到Telegram | TaskFlaw适配器 |

### 3. 集成方式

#### 方式A: TaskFlaw 调用脚本
```bash
# 添加定时任务
python3 scripts/manager.py add "采集新闻" "every 6 hours" "python3 scripts/ingest.py" agent "main"
```

#### 方式B: DAG 工作流
```
Web界面 → 创建工作流 → 设置调度 → 自动执行
```

---

## 实施步骤

### Step 1: 安装 TaskFlaw (如果未安装)
```bash
cd ~/.openclaw/skills/taskflaw
pip install -r requirements.txt
```

### Step 2: 配置数据库迁移
```bash
python3 src/db/migrations/add_workflow_tables.py migrate
```

### Step 3: 创建定时任务
- 新闻采集任务
- LLM处理任务
- 日报生成任务

### Step 4: 创建 DAG 工作流
- 设计工作流图
- 配置节点
- 设置调度

### Step 5: 测试
- 手动触发测试
- 定时触发测试
- 监控执行日志

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| LLM调用超时 | 增加重试机制 |
| 数据库锁定 | 使用独立数据库 |
| 任务堆积 | 设置并发限制 |

---

## 预期收益

- ✅ 自动化：无需手动运行
- ✅ 定时：按计划执行
- ✅ 可视化：Web界面监控
- ✅ DAG：复杂工作流支持

---

## 时间估计

| 阶段 | 时间 |
|------|------|
| 方案确认 | 30分钟 |
| 集成配置 | 2小时 |
| 测试调优 | 1小时 |
| 总计 | ~3.5小时 |

---

## 待确认

- [ ] 调度频率是否合适
- [ ] DAG 节点设计
- [ ] 通知方式
