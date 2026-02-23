#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path

# Templates
SKILL_YAML_TEMPLATE = """name: {skill_name}
version: 0.1.0
description: >
  [TODO: 添加关于此技能的简短描述]
authors:
  - [你的名字]
"""

SKILL_MD_TEMPLATE = """---
name: {skill_name}
description: [TODO: 触发描述 - Agent 何时应该使用此技能？]
---

# {skill_title}

[TODO: 一句话总结该技能的角色和目标]

## 0. 前置条件 (Prerequisites)
<prerequisites>
1.  **配置**: 参见 `config/defaults.yaml`。
2.  **工具**: [TODO: 列出所需工具, 例如 `mcp_tiksearch`]
</prerequisites>

## 1. 角色与目标 (Role & Goals)
<role>
- **角色**: [TODO: 例如：高级工程师]
- **目标**: [TODO: 例如：生成高质量代码]
- **风格**: [TODO: 例如：简洁、专业]
</role>

## 2. 工作流 (Workflow)
<workflow>
1.  **步骤 1**: [TODO]
2.  **步骤 2**: [TODO]
</workflow>
"""

CONFIG_YAML_TEMPLATE = """# {skill_name} 的默认配置
paths:
  output_dir: "docs/output"
  template_dir: "templates/"

# 需要的环境变量
env_vars:
  - "API_KEY_NAME"
"""

README_TEMPLATE = """# {skill_title}

## 概述 (Overview)
[TODO: 技能的详细描述]

## 用法 (Usage)
说明如何使用此技能。

## 配置 (Configuration)
参见 `config/defaults.yaml` 以获取可自定义的路径和设置。
"""

def title_case(s):
    return ' '.join(word.capitalize() for word in s.replace('-', ' ').split())

def init_skill(skill_name, target_dir):
    root_path = Path(target_dir) / skill_name
    
    if root_path.exists():
        print(f"Error: Directory {root_path} already exists.")
        sys.exit(1)

    # Create directories
    dirs = [
        root_path,
        root_path / "config",
        root_path / "scripts",
        root_path / "docs",
        root_path / "tests"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")

    # Create files
    files = {
        root_path / "skill.yaml": SKILL_YAML_TEMPLATE.format(skill_name=skill_name),
        root_path / "SKILL.md": SKILL_MD_TEMPLATE.format(skill_name=skill_name, skill_title=title_case(skill_name)),
        root_path / "config/defaults.yaml": CONFIG_YAML_TEMPLATE.format(skill_name=skill_name),
        root_path / "README.md": README_TEMPLATE.format(skill_title=title_case(skill_name))
    }

    for path, content in files.items():
        path.write_text(content)
        print(f"Created: {path}")

    print(f"\n✅ Skill '{skill_name}' initialized successfully!")
    print(f"👉 Next step: Edit {root_path}/SKILL.md and {root_path}/config/defaults.yaml")

def main():
    parser = argparse.ArgumentParser(description="Initialize a new Trae Agent Skill")
    parser.add_argument("name", help="Name of the skill (kebab-case)")
    parser.add_argument("--path", default=".", help="Parent directory for the skill")
    
    args = parser.parse_args()
    
    init_skill(args.name, args.path)

if __name__ == "__main__":
    main()
