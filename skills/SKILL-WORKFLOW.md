# 技能工作流指南

> 本文档定义了项目中所有技能的协作关系、任务分级标准和执行路径。

## 1. 任务分级框架

### 1.1 任务规模分级

| 级别 | 名称 | 时间估算 | 示例 | 入口技能 |
|------|------|----------|------|----------|
| **S** | 微任务 | < 5 分钟 | 修复 typo、调整配置、添加注释 | 直接执行，无需技能 |
| **M** | 小任务 | 5-30 分钟 | 修复简单 bug、添加简单 API | `task-executor` |
| **L** | 中等任务 | 30 分钟 - 2 小时 | 新增功能模块、重构组件 | `brainstorming` → `writing-plans` |
| **XL** | 大型任务 | 2+ 小时 | 新增子系统、架构重构 | `spec-generator` → `tech-design-generator` → `writing-plans` |

### 1.2 任务复杂度判断

```
┌─────────────────────────────────────────────────────────────┐
│                    任务复杂度判断流程                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  新任务到来                                                  │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ 是否涉及新功能？ │──否──► S/M 级：task-executor          │
│  └────────┬────────┘                                        │
│           │是                                               │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ 是否需要设计？   │──否──► M 级：task-executor            │
│  └────────┬────────┘                                        │
│           │是                                               │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ 是否跨多模块？   │──否──► L 级：brainstorming            │
│  └────────┬────────┘                                        │
│           │是                                               │
│           ▼                                                 │
│      XL 级：spec-generator                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 2. 技能执行流程图

### 2.1 完整工作流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           完整技能工作流                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                           │
│  │ 需求/任务输入 │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        阶段 1: 规划设计                                │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │   XL 任务                    L 任务                 M/S 任务         │   │
│  │      │                         │                       │            │   │
│  │      ▼                         │                       │            │   │
│  │  spec-generator                │                       │            │   │
│  │  (PRD 文档)                    │                       │            │   │
│  │      │                         │                       │            │   │
│  │      ▼                         │                       │            │   │
│  │  tech-design-generator         │                       │            │   │
│  │  (技术设计)                    │                       │            │   │
│  │      │                         ▼                       │            │   │
│  │      └────────────────► brainstorming ◄────────────────┘            │   │
│  │                         (需求探索/设计)                              │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │                        writing-plans                                │   │
│  │                        (实施计划)                                   │   │
│  │                              │                                      │   │
│  └──────────────────────────────┼───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        阶段 2: 代码实现                                │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │         ┌─────────────────────┴─────────────────────┐               │   │
│  │         │                                           │               │   │
│  │         ▼                                           ▼               │   │
│  │  subagent-driven-development              executing-plans           │   │
│  │  (当前会话快速执行)                        (独立会话分批执行)         │   │
│  │         │                                           │               │   │
│  │         └─────────────────────┬─────────────────────┘               │   │
│  │                               │                                      │   │
│  │                               ▼                                      │   │
│  │                    test-driven-development                          │   │
│  │                    (测试驱动开发)                                    │   │
│  │                               │                                      │   │
│  │                               ▼                                      │   │
│  │                    systematic-debugging                             │   │
│  │                    (遇到问题时调用)                                  │   │
│  │                               │                                      │   │
│  └───────────────────────────────┼──────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        阶段 3: 质量保证                                │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │                    verification-before-completion                   │   │
│  │                    (完成前验证：lint/test/build)                     │   │
│  │                               │                                      │   │
│  │                               ▼                                      │   │
│  │                    requesting-code-review                           │   │
│  │                    (请求代码审查)                                    │   │
│  │                               │                                      │   │
│  │                               ▼                                      │   │
│  │                    receiving-code-review                            │   │
│  │                    (处理审查反馈)                                    │   │
│  │                               │                                      │   │
│  └───────────────────────────────┼──────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        阶段 4: 收尾归档                                │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │                    finishing-a-development-branch                   │   │
│  │                    (分支完成：合并/PR/清理)                          │   │
│  │                               │                                      │   │
│  │                               ▼                                      │   │
│  │                    sprint-manager (Sprint 结束)                     │   │
│  │                    - 代码提交检查                                    │   │
│  │                    - 核心文档更新检查                                │   │
│  │                    - Sprint 总结归档                                 │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技能调用关系

| 当前技能 | 完成后调用 | 条件 |
|----------|-----------|------|
| `spec-generator` | `tech-design-generator` | PRD 完成后 |
| `tech-design-generator` | `writing-plans` | 技术设计完成后 |
| `brainstorming` | `writing-plans` | 设计方案批准后 |
| `writing-plans` | `subagent-driven-development` 或 `executing-plans` | 计划完成后 |
| `subagent-driven-development` | `verification-before-completion` | 实现完成后 |
| `executing-plans` | `verification-before-completion` | 实现完成后 |
| `verification-before-completion` | `requesting-code-review` | 验证通过后 |
| `requesting-code-review` | `finishing-a-development-branch` | 审查通过后 |
| `finishing-a-development-branch` | `sprint-manager` (如果是 Sprint 最后任务) | 分支合并后 |

## 3. Sprint 生命周期

### 3.1 Sprint 启动检查清单

```markdown
## Sprint 启动检查

- [ ] 上一 Sprint 已正确归档
- [ ] 目标和里程碑已确认
- [ ] 任务已从 Backlog 拉取
- [ ] 每个任务已标注优先级 (P0/P1/P2)
- [ ] 每个任务已标注规模 (S/M/L/XL)
```

### 3.2 Sprint 结束检查清单

```markdown
## Sprint 结束检查

### 代码检查
- [ ] `git status` 无未提交的代码变更
- [ ] 所有代码已按功能模块提交
- [ ] 提交信息符合 Conventional Commits 规范

### 文档检查
- [ ] 核心文档是否需要更新？（参照 kanban.md 文档索引）
  - [ ] 技术架构 `docs/tech/architecture.md`
  - [ ] API 参考 `docs/api-reference.md`
  - [ ] 数据模型 `docs/tech/data_model.md`
- [ ] 如有过时文档，已添加到下一 Sprint Backlog

### 归档检查
- [ ] Sprint 总结已创建 `docs/sprints/sprint-N-summary.md`
- [ ] kanban.md 已更新（任务移至历史）
- [ ] 未完成任务已回退到 Backlog
```

## 4. 任务执行规范

### 4.1 任务卡片格式

```markdown
#### TASK-N: 任务标题 (优先级)

**规模**: S/M/L/XL
**入口技能**: task-executor / brainstorming / spec-generator

**说明**: 任务描述

**子任务**:
- [ ] 子任务 1
- [ ] 子任务 2

**交付产物**: {任务完成后补充}
```

### 4.2 任务执行流程

```
1. 确定任务规模 (S/M/L/XL)
       │
       ▼
2. 选择入口技能
       │
       ▼
3. 按技能指引执行
       │
       ▼
4. 每完成一步，更新 TodoWrite
       │
       ▼
5. 完成后调用 verification-before-completion
       │
       ▼
6. 提交代码（提供命令，等待用户确认）
```

## 5. 常见场景速查

| 场景 | 推荐流程 |
|------|----------|
| 修复简单 bug | 直接修复 → `verification-before-completion` |
| 添加简单 API | `task-executor` → 实现 → 验证 |
| 新增功能模块 | `brainstorming` → `writing-plans` → 执行 → 验证 |
| 新增子系统 | `spec-generator` → `tech-design-generator` → `writing-plans` → 执行 |
| 架构重构 | `brainstorming` (含 ADR) → `writing-plans` → 执行 → 回归测试 |
| 调研选型 | `task-executor` (Research 模式) → ADR 文档 |
| 遇到 bug | `systematic-debugging` → 修复 → 验证 |
| Sprint 结束 | `sprint-manager` (Closing 流程) |

## 6. 技能清单

### 6.1 规划设计类
| 技能 | 用途 | 输出 |
|------|------|------|
| `spec-generator` | 生成 PRD 文档 | `docs/product/*.md` |
| `tech-design-generator` | 生成技术设计 | `docs/tech/*.md` |
| `brainstorming` | 需求探索与设计 | `docs/plans/*-design.md` |
| `writing-plans` | 编写实施计划 | `docs/plans/*.md` |

### 6.2 执行开发类
| 技能 | 用途 | 特点 |
|------|------|------|
| `task-executor` | 简单任务执行 | 直接拆解执行 |
| `subagent-driven-development` | 子代理驱动开发 | 当前会话，快速迭代 |
| `executing-plans` | 分批执行计划 | 独立会话，人工检查点 |
| `dispatching-parallel-agents` | 并行任务分发 | 多任务并行 |
| `test-driven-development` | 测试驱动开发 | 先写测试 |

### 6.3 质量保证类
| 技能 | 用途 | 触发时机 |
|------|------|----------|
| `systematic-debugging` | 系统化调试 | 遇到 bug 时 |
| `verification-before-completion` | 完成前验证 | 声称完成前 |
| `requesting-code-review` | 请求代码审查 | 功能完成后 |
| `receiving-code-review` | 处理审查反馈 | 收到反馈后 |

### 6.4 项目管理类
| 技能 | 用途 | 触发时机 |
|------|------|----------|
| `sprint-manager` | Sprint 生命周期管理 | Sprint 启动/结束 |
| `finishing-a-development-branch` | 分支完成处理 | 实现完成后 |
| `using-git-worktrees` | Git Worktree 管理 | 需要隔离工作时 |

### 6.5 元技能类
| 技能 | 用途 |
|------|------|
| `skill-creator` | 创建新技能 |
| `writing-skills` | 编写/编辑技能 |
| `using-superpowers` | 技能发现与使用 |
