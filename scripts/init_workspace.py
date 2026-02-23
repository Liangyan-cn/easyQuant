#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Default configuration matches the original hardcoded values
DEFAULT_CONFIG = {
    "paths": {
        "kanban": "kanban.md",
        "docs_root": "docs",
        "product": "docs/product",
        "tech": "docs/tech",
        "reports": "docs/reports",
        "sprints": "docs/sprints"
    },
    "files": {
        "backlog": "docs/product/backlog.md",
        "milestones": "docs/product/milestones.md"
    }
}

def load_config():
    config_path = Path("skill.config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                print(f"✅ Loaded configuration from {config_path}")
                # Simple deep merge could be implemented here, but for now we trust the user config
                # or fallback to defaults if keys are missing
                return {**DEFAULT_CONFIG, **user_config}
        except Exception as e:
            print(f"⚠️  Error loading config: {e}. Using defaults.")
    return DEFAULT_CONFIG

def init_workspace():
    print("🚀 Initializing Agent Skills Workspace...")
    
    config = load_config()
    paths = config.get("paths", DEFAULT_CONFIG["paths"])
    files = config.get("files", DEFAULT_CONFIG["files"])

    # 1. Define Directory Structure
    dirs = [
        paths["product"],
        paths["tech"],
        paths["reports"],
        paths["sprints"],
        "scripts"
    ]

    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {d}")

    # 2. Initialize kanban.md
    kanban_path = Path(paths["kanban"])
    if not kanban_path.exists() or kanban_path.stat().st_size == 0:
        kanban_content = """# Agent Project Task List

## 📝 指令 (Instructions)
- 本文件是项目进度的 **单一事实来源 (SSOT)**。
- 只有 `sprint-manager` 及其子技能可以修改此文件。
- 任务状态标记: `[ ]` (Pending), `[~]` (In Progress), `[x]` (Done).

## 🏃 Sprint 1: 初始化 (Current)
> **周期**: 2024-01-01 ~ 2024-01-14
> **目标**: 完成项目基础设施搭建
> **里程碑**: M1.0 基础架构

- [~] **环境初始化** (Priority: P0)
    - [x] 创建目录结构
    - [x] 生成 kanban.md
    - [ ] 验证 Agent Skills 协作流

## 📦 待办池 (Backlog)
* [ ] 实现用户登录功能 (P1)
* [ ] 集成支付网关 (P2)

## 🔄 周期性任务池 (Recurring Tasks Pool)
- [ ] 每周代码审查
- [ ] 每日站会记录

## 📜 历史 Sprints (Completed)
<!-- Completed sprints will be archived here -->
"""
        kanban_path.write_text(kanban_content, encoding='utf-8')
        print(f"✅ Created file: {kanban_path}")
    else:
        print(f"ℹ️  File already exists: {kanban_path}")

    # 3. Initialize Placeholder Docs
    placeholders = {
        files["milestones"]: "# Milestones\n\n## M1.0 MVP\n- [ ] Core Features\n",
        files["backlog"]: "# Product Backlog\n\n## Unsorted Ideas\n- [ ] Idea 1\n"
    }

    for path, content in placeholders.items():
        p = Path(path)
        # Ensure parent dir exists (in case file path is custom)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        if not p.exists():
            p.write_text(content, encoding='utf-8')
            print(f"✅ Created file: {p}")
        else:
            print(f"ℹ️  File already exists: {p}")

    print("\n✨ Workspace initialization complete! You are ready to sprint.")

if __name__ == "__main__":
    init_workspace()
