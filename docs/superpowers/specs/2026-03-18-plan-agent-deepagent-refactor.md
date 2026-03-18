# PlanAgent 改造设计 - 基于 DeepAgents

**日期**: 2026-03-18
**作者**: Claude Code
**状态**: 已批准

---

## 1. 概述

将 `plan_agent.py` 从简单的 LLM 直接调用改造为基于 DeepAgents 框架实现，使用 skill 机制提供周计划创建能力。

## 2. 改造目标

1. 使用 `deepagents` 的 `create_deep_agent` 替代简单的 `llm.ainvoke()`
2. 创建周计划 skill (`weekly_plan`) 提供结构化计划创建能力
3. 使用 `FilesystemBackend` 读取本地 skill 文件
4. 调整系统提示词以配合 skill 工作

## 3. 架构设计

### 3.1 目录结构

```
src/features/plan/
├── plan_agent.py          # PlanAgent 主文件（改造）
└── skills/
    └── weekly_plan/
        └── SKILL.md       # 周计划 skill 定义
```

### 3.2 组件关系

```
PlanAgent (BaseExecutor)
    └── create_deep_agent()
        ├── model: qwen3.5-plus (via create_llm())
        ├── skills: ["./skills/"]
        ├── backend: FilesystemBackend (root: src/features/plan/skills/)
        └── system_prompt: 调整后的 PLAN_AGENT
```

## 4. 详细设计

### 4.1 PlanAgent 改造

**文件**: `src/features/plan/plan_agent.py`

**关键改动**:
- 移除直接的 `llm.ainvoke()` 调用
- 使用 `create_deep_agent` 创建 agent 实例
- 配置 `FilesystemBackend` 指向 skills 目录
- 支持 skill 按需加载

### 4.2 周计划 Skill

**文件**: `src/features/plan/skills/weekly_plan/SKILL.md`

**格式**: DeepAgents 官方 SKILL.md 格式

**内容**:
- YAML Frontmatter: `name`, `description`
- Body: 周计划创建的工作流指导

### 4.3 提示词调整

**文件**: `src/features/prompts.py`

**调整方向**:
- 保留核心能力描述
- 增加 skill 使用引导
- 简化通用描述，让 skill 主导具体行为

## 5. 依赖项

- `deepagents` 包（用户已安装）
- `FilesystemBackend` 来自 `deepagents.backends`

## 6. 测试要点

1. PlanAgent 能正确加载
2. Skill 能被 deepagent 识别和使用
3. 周计划创建功能正常工作

## 7. 向后兼容

- 保持 `@plan` 命令不变
- 保持关键词匹配不变
- 保持 `BaseExecutor` 接口不变

## 8. 实施状态

- [x] 设计文档创建
- [x] 周计划 skill 创建 (`src/features/plan/skills/weekly_plan/SKILL.md`)
- [x] PlanAgent 改造 (`src/features/plan/plan_agent.py`)
- [x] 提示词调整 (`src/features/prompts.py`)
- [x] 测试验证通过

## 9. 测试结果

```
✓ PlanAgent 导入成功
✓ Agent 注册成功 (plan_agent)
✓ 意图识别测试通过 ("帮我创建一个周计划" → plan_agent, 置信度 0.4)
✓ pytest tests/integration/test_intent.py PASSED
```
