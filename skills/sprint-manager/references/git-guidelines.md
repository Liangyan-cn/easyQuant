# Git Operations Guidelines

本指南规范了 Sprint 结束时的代码提交流程，确保代码仓库的整洁与安全。

## 1. Pre-Commit Check (Diff Evaluation)
在执行任何提交之前，必须运行 `git status` 和 `git diff` 来评估变更。

### 1.1 忽略策略 (Ignore Strategy)
以下类型的文件 **严禁** 提交到代码仓库，必须添加到 `.gitignore`：
*   **临时文件**: IDE 配置 (`.vscode/`, `.idea/`, `.trae/`), 系统缓存 (`.DS_Store`, `__pycache__/`)。
*   **敏感数据**: API Keys (`.env`), 包含 PII 的日志 (`logs/`), 数据库文件。
*   **生成产物**: 编译结果 (`build/`, `dist/`), 覆盖率报告 (`htmlcov/`), 临时评测中间文件 (`data/eval/failed_cases.json`)。
*   **大文件**: 超过 100MB 的数据集或模型权重（除非使用 Git LFS）。

### 1.2 强制检查清单
- [ ] 运行 `git status` 查看未跟踪文件 (Untracked Files)。
- [ ] 识别出不应提交的目录/文件。
- [ ] 如果发现不合规文件，立即更新 `.gitignore`。
- [ ] 再次运行 `git status` 确认 `.gitignore` 生效。

## 2. Commit Message Convention
提交信息必须清晰描述变更内容，建议遵循以下格式：

```
<Type>: <Subject>

<Body> (Optional)
```

### Type 列表
*   `feat`: 新功能 (New Feature)
*   `fix`: 修复 Bug (Bug Fix)
*   `docs`: 文档变更 (Documentation)
*   `style`: 代码格式调整 (Formatting, missing semi colons, etc)
*   `refactor`: 代码重构 (Refactoring)
*   `test`: 测试用例变更 (Adding missing tests)
*   `chore`: 构建过程或辅助工具变更 (Build tasks, package manager configs)

### 示例
```bash
# 好的示例
git commit -m "feat: Add Intent Router evaluation script"
git commit -m "docs: Update benchmark report for Sprint 10"
git commit -m "chore: Update .gitignore to exclude eval temp files"

# 坏的示例
git commit -m "update"
git commit -m "fix bug"
```

## 3. Sprint Closing Workflow
在 Sprint 结束生成 Summary 时，必须包含代码提交建议：

1.  **Review Changes**:
    ```bash
    git status
    git diff --stat
    ```
2.  **Update Ignore**:
    (如果发现垃圾文件)
    ```bash
    echo ".trae/" >> .gitignore
    ```
3.  **Recommend Commit (Console Only)**:
    生成可以直接运行的 Git 命令建议，但**仅作为 Console Warning 输出**，**严禁**包含在 `sprint_N_summary.md` 中。
    **强烈建议**根据文件类型（docs, src, config）生成多条提交建议，而不是“一键提交所有”。

```bash
# Example Recommendation
# Option 1: Simple
git add .
git commit -m "feat: Complete Sprint 10 (Intent Baseline)"

# Option 2: Split (Recommended)
git add docs/
git commit -m "docs: Add Sprint 10 Summary"
git add src/
git commit -m "feat: Implement Intent Router"
```
