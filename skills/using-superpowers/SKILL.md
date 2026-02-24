---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
---

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## How to Access Skills

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.

**In other environments:** Check your platform's documentation for how skills are loaded.

# Using Skills

## The Rule

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means that you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to use it.

```dot
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "About to EnterPlanMode?" [shape=doublecircle];
    "Already brainstormed?" [shape=diamond];
    "Invoke brainstorming skill" [shape=box];
    "Might any skill apply?" [shape=diamond];
    "Invoke Skill tool" [shape=box];
    "Announce: 'Using [skill] to [purpose]'" [shape=box];
    "Has checklist?" [shape=diamond];
    "Create TodoWrite todo per item" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond (including clarifications)" [shape=doublecircle];

    "About to EnterPlanMode?" -> "Already brainstormed?";
    "Already brainstormed?" -> "Invoke brainstorming skill" [label="no"];
    "Already brainstormed?" -> "Might any skill apply?" [label="yes"];
    "Invoke brainstorming skill" -> "Might any skill apply?";

    "User message received" -> "Might any skill apply?";
    "Might any skill apply?" -> "Invoke Skill tool" [label="yes, even 1%"];
    "Might any skill apply?" -> "Respond (including clarifications)" [label="definitely not"];
    "Invoke Skill tool" -> "Announce: 'Using [skill] to [purpose]'";
    "Announce: 'Using [skill] to [purpose]'" -> "Has checklist?";
    "Has checklist?" -> "Create TodoWrite todo per item" [label="yes"];
    "Has checklist?" -> "Follow skill exactly" [label="no"];
    "Create TodoWrite todo per item" -> "Follow skill exactly";
}
```

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought                             | Reality                                                |
| ----------------------------------- | ------------------------------------------------------ |
| "This is just a simple question"    | Questions are tasks. Check for skills.                 |
| "I need more context first"         | Skill check comes BEFORE clarifying questions.         |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first.           |
| "I can check git/files quickly"     | Files lack conversation context. Check for skills.     |
| "Let me gather information first"   | Skills tell you HOW to gather information.             |
| "This doesn't need a formal skill"  | If a skill exists, use it.                             |
| "I remember this skill"             | Skills evolve. Read current version.                   |
| "This doesn't count as a task"      | Action = task. Check for skills.                       |
| "The skill is overkill"             | Simple things become complex. Use it.                  |
| "I'll just do this one thing first" | Check BEFORE doing anything.                           |
| "This feels productive"             | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means"            | Knowing the concept ≠ using the skill. Invoke it.      |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach the task
2. **Implementation skills second** (frontend-design, mcp-builder) - these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → debugging first, then domain-specific skills.

## Skill Types

**Rigid** (TDD, debugging): Follow exactly. Don't adapt away discipline.

**Flexible** (patterns): Adapt principles to context.

The skill itself tells you which.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.

## Sprint-Driven Workflow (easyQuant)

本项目以 **sprint-manager** 为核心驱动技能使用：

```
Sprint 启动 → brainstorming → writing-plans → TDD → code-review → verification → Sprint 结束
     ↑                                                                              ↓
     └──────────────────────────────────────────────────────────────────────────────┘
```

### 技能选择决策树

**功能开发场景：**
```
需要开发新功能?
    │
    ├─ 有现成 PRD? ─── No ──→ prd-generator (生成PRD)
    │       │                      ↓
    │      Yes              tech-doc-generator
    │       │                      ↓
    │       ├─ 有技术设计? ─ No ──→ tech-doc-generator
    │       │       │
    │       │      Yes
    │       │       │
    │       └───────┴─ 需要探索讨论? ─ Yes ──→ brainstorming
    │                       │
    │                      No
    │                       ↓
    └─────────────────→ writing-plans (编写实施计划)
```

**任务复杂度判断：**
```
任务复杂吗?
    │
    ├─ 简单任务 (< 3步) ──→ task-skills (直接执行)
    │
    └─ 复杂任务 (≥ 3步) ──→ brainstorming → writing-plans
```

### 快速决策表

| 用户意图                | 首选技能                         | 备选技能        |
| ----------------------- | -------------------------------- | --------------- |
| 开始/结束 Sprint        | `sprint-manager`                 | -               |
| 新功能 (需求模糊)       | `prd-generator`                  | `brainstorming` |
| 新功能 (需求清晰)       | `brainstorming`                  | `writing-plans` |
| 简单任务                | `task-skills`                    | -               |
| 有计划要执行 (独立会话) | `executing-plans`                | -               |
| 有计划要执行 (当前会话) | `subagent-driven-development`    | -               |
| 遇到 bug                | `systematic-debugging`           | -               |
| 写代码                  | `test-driven-development`        | -               |
| 代码完成                | `requesting-code-review`         | -               |
| 收到审查反馈            | `receiving-code-review`          | -               |
| 声称完成                | `verification-before-completion` | -               |

### 技能链路图

```
prd-generator ──→ tech-doc-generator ──→ writing-plans
                                              │
brainstorming ────────────────────────────────┤
                                              │
task-skills ──────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
            executing-plans                              subagent-driven-development
            (独立会话执行)                                    (当前会话执行)
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                              test-driven-development
                                              │
                                              ▼
                              requesting-code-review
                                              │
                                              ▼
                              receiving-code-review
                                              │
                                              ▼
                          verification-before-completion
                                              │
                                              ▼
                        finishing-a-development-branch
```

详见: `.trae/skills/SKILLS-GUIDE.md`
