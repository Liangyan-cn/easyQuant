---
name: skill-creator
description: "[Meta Skill] 用于创建、初始化和标准化新的 Sprint.AI Skills。当用户想要开发新能力或标准化现有能力时调用。"
---

# Skill Creator

本技能旨在帮助开发者快速创建符合 **Sprint.AI** 标准的技能。它强制执行"约定优于配置"的最佳实践，确保所有技能具有一致的结构和可维护性。

## 0. Prerequisites
<prerequisites>
1.  **Environment**: Python 3.8+ (推荐)
2.  **Tools**: `git` (用于版本控制)
</prerequisites>

## 1. Capabilities

### 🆕 初始化新技能 (Initialize Skill)
**触发条件**: "创建一个新技能", "Init new skill", "Scaffold a skill".
**动作**:
1.  运行 `python3 skill-creator/scripts/init_skill.py <skill_name>`。
2.  生成标准的目录结构：
    *   `skill.yaml`: 元数据定义。
    *   `SKILL.md`: 核心指南模板。
    *   `config/defaults.yaml`: 默认配置（路径、环境变量）。
    *   `scripts/`: 辅助脚本目录。
    *   `docs/`: 参考文档目录。

### 🔍 验证技能 (Validate Skill)
**触发条件**: "验证技能格式", "Check skill structure".
**动作**:
1.  检查 `skill.yaml` 是否存在且格式正确。
2.  检查 `SKILL.md` 是否包含 `<prerequisites>` 和 `<role>` 标签。
3.  验证目录结构是否符合标准。

## 2. Standard Structure (Generated)

生成的技能将遵循以下结构：

```text
skill-name/
├── skill.yaml          # [必须] 技能元数据 (name, description, version)
├── SKILL.md            # [必须] 技能核心指南 (Prompt)
├── config/             # [推荐] 配置文件
│   └── defaults.yaml   # 默认路径和变量定义
├── scripts/            # [可选] Python/Shell 脚本
├── docs/               # [可选] 详细参考文档
└── README.md           # [自动生成] 使用说明
```

## 3. Best Practices

1.  **配置分离**: 永远不要在 `SKILL.md` 中硬编码路径。将其放入 `config/defaults.yaml`。
2.  **依赖声明**: 在 `SKILL.md` 头部明确声明 `<prerequisites>`。
3.  **原子性**: 一个 Skill 应该只做一件事（例如：`pdf-parser` vs `file-manager`）。
