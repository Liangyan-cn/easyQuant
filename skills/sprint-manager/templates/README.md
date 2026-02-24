# 文档模板库

本目录包含了 Sprint.AI 项目的所有标准文档模板。使用这些模板可以确保文档的一致性和完整性。

## 📋 模板列表

### 产品规格文档 (Product Spec)

*   **[prd_standard.md](prd_standard.md)**: 标准 Product Spec 模板
    *   **适用场景**: 复杂功能开发,需要完整调研和详细需求
    *   **包含章节**: 背景与价值, 用户故事, 功能需求, 非功能需求, 验收标准
    *   **预计填写时间**: 30-60 分钟

*   **[prd_lightweight.md](prd_lightweight.md)**: 轻量 Product Spec 模板
    *   **适用场景**: Bug 修复, 小调整, 简单功能
    *   **包含章节**: 变更描述, 验收标准, 执行指引
    *   **预计填写时间**: 5-10 分钟

### 技术设计文档 (Technical Design)

*   **[tech_design.md](tech_design.md)**: Technical Design 模板
    *   **适用场景**: 所有需要技术设计的功能
    *   **包含章节**: 技术调研, 方案对比, 架构设计, 核心设计, 测试验证
    *   **预计填写时间**: 60-120 分钟

### Sprint 管理文档

*   **[sprint_planning.md](sprint_planning.md)**: Sprint 计划模板
    *   **适用场景**: Sprint 启动时使用
    *   **包含章节**: Sprint Goal, 容量评估, 任务列表, 风险评估
    *   **预计填写时间**: 30-45 分钟

*   **[sprint_summary.md](sprint_summary.md)**: Sprint 总结模板
    *   **适用场景**: Sprint 结束时使用
    *   **包含章节**: 数据统计, 评审清单, 复盘, 任务归档
    *   **预计填写时间**: 45-60 分钟

*   **[task_template.md](task_template.md)**: 任务卡片模板 ⭐ NEW
    *   **适用场景**: 创建和管理 Sprint 任务
    *   **包含章节**: 任务说明, 依赖关系, 子任务, 交付产物
    *   **预计填写时间**: 5-15 分钟
    *   **特点**: 交付产物可在任务完成后补充

*   **[daily_standup.md](daily_standup.md)**: 每日站会模板
    *   **适用场景**: 每日进度同步
    *   **包含章节**: 进度概览, 成员更新, 阻塞项, 重点任务
    *   **预计填写时间**: 10-15 分钟

### 调研与决策文档

*   **[research_report.md](research_report.md)**: 调研报告模板
    *   **适用场景**: 技术选型, 可行性研究, 竞品分析
    *   **包含章节**: 研究目标, 竞品分析, 技术趋势, 综合分析, 行动计划
    *   **预计填写时间**: 120-180 分钟

*   **[adr_template.md](adr_template.md)**: 架构决策记录 (ADR) 模板
    *   **适用场景**: 重要技术决策记录
    *   **包含章节**: 上下文, 决策, 候选方案, 后果, 演进路线
    *   **预计填写时间**: 30-45 分钟

## 🎯 使用指南

### 1. 选择合适的模板

根据任务类型选择对应的模板:

```
功能开发 → prd_standard.md + tech_design.md
Bug 修复 → prd_lightweight.md
技术选型 → research_report.md + adr_template.md
Sprint 管理 → sprint_planning.md + sprint_summary.md
```

### 2. 复制模板

```bash
# 复制 Product Spec 模板
cp skills/spec-generator/templates/prd_standard.md docs/product/feature_name.md

# 复制 Technical Design 模板
cp skills/tech-design-generator/templates/tech_design.md docs/tech/feature_name_design.md
```

### 3. 填写模板

*   **保留结构**: 不要删除章节标题,即使某些章节暂时为空
*   **使用占位符**: 用 `<描述>` 标记需要填写的内容
*   **添加链接**: 在"相关文档"章节添加文档间的链接
*   **使用 Checklist**: 用 `[ ]` 标记待办事项

### 4. 模板定制

如果标准模板不适合你的项目,可以:

1.  复制模板到项目根目录
2.  修改章节结构
3.  在 `skill.config.json` 中指定自定义模板路径

## 📊 模板对比

| 模板                | 复杂度 | 填写时间   | 适用场景    | 必填章节 |
| ------------------- | ------ | ---------- | ----------- | -------- |
| **prd_standard**    | ⭐⭐⭐⭐   | 30-60min   | 复杂功能    | 1,2,3,5  |
| **prd_lightweight** | ⭐      | 5-10min    | 简单任务    | 1,2      |
| **tech_design**     | ⭐⭐⭐⭐⭐  | 60-120min  | 所有功能    | 0,1,2,3  |
| **sprint_planning** | ⭐⭐⭐    | 30-45min   | Sprint 启动 | 1,2,3    |
| **sprint_summary**  | ⭐⭐⭐    | 45-60min   | Sprint 结束 | 1,2,3    |
| **task_template**   | ⭐⭐      | 5-15min    | 任务管理    | 1,2      |
| **research_report** | ⭐⭐⭐⭐   | 120-180min | 技术调研    | 1,2,3,6  |
| **adr_template**    | ⭐⭐⭐    | 30-45min   | 重要决策    | 1,2,3,4  |

## 🔍 模板验证

### 自动验证脚本

```bash
# 验证 PRD 格式
python scripts/validate_prd.py docs/product/feature_name.md

# 验证 Tech Design 格式
python scripts/validate_tech_design.py docs/tech/feature_name_design.md
```

### 手动验证清单

**Product Spec 验证**:
*   [ ] 是否有明确的用户故事?
*   [ ] 验收标准是否可衡量?
*   [ ] 是否包含相关文档链接?

**Technical Design 验证**:
*   [ ] 是否对比了至少 2 个方案?
*   [ ] 是否定义了 Pydantic 模型?
*   [ ] 是否包含测试策略?

## 📝 最佳实践

### 1. 文档命名规范

```
Product Spec: <feature_name>.md
Technical Design: <feature_name>_design.md
Sprint Summary: sprint_<N>_summary.md
Research Report: <topic>_research.md
ADR: adr_<NNN>_<title>.md
```

### 2. 文档存放位置

```
docs/
├── product/          # Product Spec 文档
├── tech/             # Technical Design 文档
├── reports/          # Sprint 总结和调研报告
└── decisions/        # ADR 文档
```

### 3. 文档更新频率

*   **Product Spec**: 需求变更时更新
*   **Technical Design**: 架构调整时更新
*   **Sprint Summary**: Sprint 结束时创建
*   **Daily Standup**: 每日更新
*   **ADR**: 重要决策时创建

## 🤝 贡献新模板

如果你创建了新的有用模板,欢迎贡献:

1.  在相应技能的 `templates/` 目录下创建新模板（如 `skills/spec-generator/templates/`）
2.  在本 README 中添加说明
3.  提供使用示例
4.  提交 PR

## 📚 相关文档

*   **文档管理指南**: [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md)
*   **文档索引**: [INDEX.md](../INDEX.md)
*   **项目 README**: [README.md](../../README.md)
