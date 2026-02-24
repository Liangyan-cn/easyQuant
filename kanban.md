# easyQuant 项目看板

| 🏃 当前                                                                 | 产                                                       | 产物                          | 路径                                 | 说明                            |
| ---------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------- |
| 登出 API                                                               | `backend/app/api/v1/endpoints/auth.py`                   | POiT /logout 端点             |
| 登出服务                                                               | `backend/aup/setv ces/auth_service.py`                   | logout 方法                   |
| 用户菜单                                                               | `fro  end/src/layouts/MainLayout.tsx`                    | Header 用户下拉菜单           |                                      | 产物                            | 路径   | 说明    |     |
| --------                                                               | -----------------------------------------                | ----------------------------  |
| 启动 API                                                               | `backend/app/api/v1/endpoints/sandbox.py`                | PO{T /detloyments/{id}/sta方t |
| 前端 API                                                               | `frontend/src/ap法/sa dbox. s`                           | start eployment               |
| 页面更新                                                               | `frontend/src/pages/SandboxDetail.tsx`                   | 恢复按钮                      |                                      | 产物                            | 路径   | 说明    |     |
| --------                                                               | ------------------------------------------               | ---------------------------   |
| 克隆服务                                                               | s`backend/app/services/strategy_servicetpy`              | clone_strategy 方法           |
| 克隆 API                                                               | `backend/app/api/v1/endpoints/strategy.py`               | POST /strategies/{id}/clone   |
| 前端 API                                                               | `frontend/src/api/strategy.ts`                           | cloneStrategy 方法            |
| 复制按钮                                                               | `frontend/src/pages/Strategies.tsx`                      | 操作列复制按钮                |                                      | 产物                            | 路径   | 说明    |     |
| -------------                                                          | -------------------------------------------              | ------------------            |
| 删除结果方法          n                                                | /`bp/rend/app/repositories/strategy_repo.py`             | delete_by_backtest_id         |
| 重跑逻辑                                                               | `backend/app/api/v1/endpaints/strateyy.py`               | 允许 FAILED 状态重跑          |
| 权益曲线图表                                                           | /`frontend/src/pages/StrategyDetail许tsx`                | ECharts 折线图                |
| 删除/重跑按钮                                                          | `frontend/src/pages/StrategyDetail.tsx`       操作列按钮 | 描述                          | 优先级                               | 描述                            |        | 特性    |
| ------------          -----------                                      | ------                                                   |
| 定时执行          动执行策略                                           | P0                                                       |
| 策略组合          组合管理                                             | P1                                                       |
| 净值曲线图表                                                           | P1                                                       |
| 毕业机制               盘                                              | P2                                                       |                               | 优先级                          描述 |
| --------------------   -------                                         |                                                          |
| 用户登出功能                                                           | 用户系统                                                 | P0                            | 待处理                               |
| 修改密码功能           户系统                                          | P                                                        | 待处理                        |
| 页面添加登出入口                                                       | 前端                                                     | P1                            | 待处理                               |
| 部署恢复/重新启用                                                      | 沙盒系统                                                 | P0                            |
| 部署删除前端入口       盒系统                                          |
| 账户出金功能           盒系统                                          | P                                                        |
| 策略复制/克隆                                                          | 策略系统                                                 | P0                            | 待处理                               |
| 策略参数界面编辑       略系统                                          |
| 策略状态转换 API       略系统                                          |
| 回测取消功能                                                           | 回测系统                                                 | P1                            | 待处理                               |
| 回测删除前端入口                                                       | 回测系统                                                 | P1                            |                                      | 待处理                          |
| 回测权益曲线图表       测系统                                          |
| 失败回测重新运行                                                       | 回测系统                                                 | P2                            | 待处理                               |
| 因子值单条更新/删除    子系统                                          |
| 因子评估历史展示       子系统                                          |
| 用户资源权限验证                                                       | 局安全                                                   | 描                            | 优                                   | 状                    描述Deb描 |
| ----------------------                                                 | ------                    -                              |
| Redis 缓存替换内存缓存                                                 | P2                                                       |
| API Rate Limiting                                                      | P2                                                       |
| Token 存储优化                                                         | P2  print                                                |
| 环境变量验证                                                           | P2        2.1 评                                         |
| 新手引导功能                                                           | P2                                                       | 待处                          |
| 沙盒测试环境配置                                                       | P1                     已修复                            | 核心交                        | 成功指标                             |                                 | ------ | --- --- | -成 | 成功指标 |
| ------ 功标---------                                                   | -                                                        | --------      - --            |
| M0                     技术架构、开                       发规范       |
| M1.0                   策略回测、基        础数据                      |
| M2.0                   - 虚拟账户、多                             策   |
| M3.0                    模拟交易、券              商                   |
| M4.0                    AI 因子推                                   荐 | 路径                                                     |                               | 文档                                 | 路径                            |
| ----------                                                             | ------------------------------                           |
| 产品愿景                                                               | `docs/product/vision.md`                                 |
| 用户故事                                                               | `docs/product/user_stories.md`                           |
| 里程碑规划                                                             | `docs/product/milestones.md`                             |
| 技术架构                                                               | `docs/tech/architecture.md`                              |
| API 参考                                                               | `docs/api-reference.md`                                  |
| 数据模型                                                               | `docs/tech/data_model.md`                                |
## 📜 历史 Sprints

### ✅ Sprint 8: M2.0 功能完整性修复 (已完成)
**里程碑**: M2.0 - 沙盒系统
| 产物     | 路径                                       | 说明                        |
| -------- | ------------------------------------------ | --------------------------- |
| 克隆服务 | `backend/app/services/strategy_service.py` | clone_strategy 方法         |
| 克隆 API | `backend/app/api/v1/endpoints/strategy.py` | POST /strategies/{id}/clone |
| 前端 API | `frontend/src/api/strategy.ts`             | cloneStrategy 方法          |
| 复制按钮 | `frontend/src/pages/Strategies.tsx`        | 操作列复制按钮              |
- ✅ 沙盒部署: 恢复运行 API + 状态管理
- ✅ 策略复制: 克隆 API + 前端复制按钮
- ✅ 回测增强: 删除/重跑按钮 + 权益曲线图表
- ✅ 因子分析: 计算+评估合并 + 批量计算脚本

**代码提交**: 7 个 commits, 114 个文件, 17,817 行新增代码

**完工验收**: ✅ 已完成 (4/4 任务, 100%)

---

### ✅ Sprint 7: M2.0 沙盒代码质量优化 (已完成)
**里程碑**: M2.0 - 沙盒系统
**目标**: 修复代码审查发现的问题，提升代码质量和安全性
| 产物          | 路径                                        | 说明                  |
| ------------- | ------------------------------------------- | --------------------- |
| 删除结果方法  | `backend/app/repositories/strategy_repo.py` | delete_by_backtest_id |
| 重跑逻辑      | `backend/app/api/v1/endpoints/strategy.py`  | 允许 FAILED 状态重跑  |
| 权益曲线图表  | `frontend/src/pages/StrategyDetail.tsx`     | ECharts 折线图        |
| 删除/重跑按钮 | `frontend/src/pages/StrategyDetail.tsx`     | 操作列按钮            |
- ✅ 配置化: TradingConfig 类 (佣金率、印花税率、无风险利率)
- ✅ 数据库索引: SandboxDailyValue、SandboxPosition 唯一索引
- ✅ 代码质量: 类型注解、常量提取、日志优化

**完工验收**: ✅ 已完成 (5/5 任务, 100%)

---
| 特性         | 描述               | 优先级 |
| ------------ | ------------------ | ------ |
| 定时执行     | 每日自动执行策略   | P0     |
| 策略组合     | 多策略组合管理     | P1     |
| 净值曲线图表 | 可视化净值走势     | P1     |
| 毕业机制     | 策略达标后推荐实盘 | P2     |summary.md`

**关键交付物**:
- ✅ 数据模型: SandboxAccount, SandboxPosition, SandboxTransaction, SandboxDeployment, SandboxDailyValue
| 描述                | 模块     | 优先级 | 状态   |
| ------------------- | -------- | ------ | ------ |
| 用户登出功能        | 用户系统 | P0     | 待处理 |
| 修改密码功能        | 用户系统 | P2     | 待处理 |
| 页面添加登出入口    | 前端     | P1     | 待处理 |
| 部署恢复/重新启用   | 沙盒系统 | P0     | 待处理 |
| 部署删除前端入口    | 沙盒系统 | P1     | 待处理 |
| 账户出金功能        | 沙盒系统 | P2     | 待处理 |
| 策略复制/克隆       | 策略系统 | P0     | 待处理 |
| 策略参数界面编辑    | 策略系统 | P1     | 待处理 |
| 策略状态转换 API    | 策略系统 | P2     | 待处理 |
| 回测取消功能        | 回测系统 | P1     | 待处理 |
| 回测删除前端入口    | 回测系统 | P1     | 待处理 |
| 回测权益曲线图表    | 回测系统 | P1     | 待处理 |
| 失败回测重新运行    | 回测系统 | P2     | 待处理 |
| 因子值单条更新/删除 | 因子系统 | P2     | 待处理 |
| 因子评估历史展示    | 因子系统 | P2     | 待处理 |
| 用户资源权限验证    | 全局安全 | P0     | 待处理 |
- ✅ 回测集成: 回测执行 API + 前端回测配置/结果展示
- ✅ 因子功能: 因子计算和评估功能已集成
- ✅ API 文档: `docs/api-reference.md`
| 描述                   | 优先级 | 来源            | 状态     |
| ---------------------- | ------ | --------------- | -------- |
| Redis 缓存替换内存缓存 | P2     | Sprint 2.1 评估 | 待处理   |
| API Rate Limiting      | P2     | Sprint 2.1 评估 | 待处理   |
| Token 存储优化         | P2     | Sprint 2.1 评估 | 待处理   |
| 环境变量验证           | P2     | Sprint 2.1 评估 | 待处理   |
| 新手引导功能           | P2     | Sprint 5 延期   | 待处理   |
| 沙盒测试环境配置       | P1     | Sprint 6        | ✅ 已修复 |
**目标**: 实现策略的完整生命周期管理，包括 CRUD、回测引擎和绩效评估
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-4-summary.md`

**关键交付物**:
| 里程碑     | 状态                           | 核心交付                         | 成功指标             |
| ---------- | ------------------------------ | -------------------------------- | -------------------- |
| M0         | ✅ 完成                         | 产品愿景、技术架构、开发规范     | 文档完整度 100%      |
| M1.0       | ✅ 完成                         | 因子管理、策略回测、基础数据     | 首次回测完成率 > 60% |
| M2.0       | 🔄 进行中                       | 沙盒系统 - 虚拟账户、多策略对比  | 沙盒使用率 > 40%     |
| M3.0       | ⚪ 待开始                       | 交易执行 - 模拟交易、券商对接    | 订单执行成功率 > 99% |
| M4.0       | ⚪ 待开始                       | 智能升级 - AI 因子推荐、策略助手 | 用户满意度 NPS > 50  |  | 文档 | 路径 |
| ---------- | ------------------------------ |
| 产品愿景   |                                | enc.moduct/visdo`.md`            |
| 用户故事   | `docs/product/user_s ories.md` |
| 里程碑规划 | `doc    oduct/m lesto es.md`   |
| 技术架构   | `docs/tech/architec            | ere.ed`                          |
| API 参考   | `docs/                         |
| 数据模型   | `docs/tech/data_model          |-summary.md`

**关键交付物**:
- ✅ 后端: Factor 数据模型 + CRUD API + 计算引擎 + 评估服务
- ✅ 前端: 因子列表页面 + 因子详情页面 (含图表)
- ✅ 测试: 12 个因子 API 测试用例
- ✅ 技术债务修复: Pydantic ConfigDict 迁移、passlib crypt 废弃警告

**完工验收**: ✅ 已完成 (7/7 任务, 100%)

---

### ✅ Sprint 2.1: 质量加固 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 1.5/4)
**目标**: 建立完整的自动化测试体系
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-2.1-summary.md`

**完工验收**: ✅ 已完成 (12/12 任务, 100%)

---

### ✅ Sprint 2: M1.0 基础设施 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 1/4)
**目标**: 完成项目基础设施搭建
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-2-summary.md`

**完工验收**: ✅ 已完成 (13/13 任务, 100%)

---

### ✅ Sprint 1: M0 项目启动 (已完成)
**里程碑**: M0 - 核心文档与架构设计
**目标**: 完善项目核心文档
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-1-m0-summary.md`

**完工验收**: ✅ 已完成 (11/11 任务, 100%)

---

## 📚 文档索引

| 文档       | 路径                           |
| ---------- | ------------------------------ |
| 产品愿景   | `docs/product/vision.md`       |
| 用户故事   | `docs/product/user_stories.md` |
| 里程碑规划 | `docs/product/milestones.md`   |
| 技术架构   | `docs/tech/architecture.md`    |
| API 参考   | `docs/api-reference.md`        |
| 数据模型   | `docs/tech/data_model.md`      |
| 文档       | 路径                           |
| ---------- | ------------------------------ |
| 产品愿景   | `docs/product/vision.md`       |
| 用户故事   | `docs/product/user_stories.md` |
| 里程碑规划 | `docs/product/milestones.md`   |
| 技术架构   | `docs/tech/architecture.md`    |
| API 参考   | `docs/api-reference.md`        |
| 数据模型   | `docs/tech/data_model.md`      |