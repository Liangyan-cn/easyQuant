# 沙盒净值曲线图表设计文档

## 概述

在沙盒账户详情页面添加净值曲线图表，展示账户净值随时间变化的趋势，并与基准（沪深300）进行对比。

## 需求

- **数据展示**: 净值曲线 + 基准对比
- **图表位置**: 顶部统计卡片下方，Tab 切换上方
- **实现方式**: 纯前端实现，使用现有 API 返回的 `daily_values` 数据

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   SandboxDetail.tsx                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │           账户概览卡片 (现有)                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │           NetValueChart (新增)                    │    │
│  │   净值曲线 + 基准对比                              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Tab 切换 (现有)                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 组件设计

### NetValueChart 组件

**文件路径**: `frontend/src/components/NetValueChart.tsx`

**Props 接口**:
```typescript
interface NetValueChartProps {
  dailyValues: SandboxDailyValue[];
  initialCapital: number;
}
```

**功能**:
- 展示净值曲线（归一化为初始值 1.0）
- 展示基准对比曲线（如有 benchmark_return 数据）
- 支持 Tooltip 显示详细数据
- 响应式布局

## 数据流

```
API Response (daily_values)
        │
        ▼
┌───────────────────┐
│ 数据转换          │
│ - 日期格式化       │
│ - 净值归一化       │
│ - 基准数据处理     │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ ECharts 配置      │
│ - xAxis: 日期     │
│ - yAxis: 净值     │
│ - series: 曲线    │
└───────────────────┘
        │
        ▼
    ReactECharts
```

## 图表配置

```typescript
const chartOption = {
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      // 显示日期、净值、收益率
    }
  },
  legend: {
    data: ['策略净值', '基准(沪深300)']
  },
  xAxis: {
    type: 'category',
    data: dates
  },
  yAxis: {
    type: 'value',
    axisLabel: { formatter: '{value}' }
  },
  series: [
    {
      name: '策略净值',
      type: 'line',
      smooth: true,
      data: netValues,
      lineStyle: { color: '#1890ff' }
    },
    {
      name: '基准(沪深300)',
      type: 'line',
      data: benchmarkValues,
      lineStyle: { color: '#999', type: 'dashed' }
    }
  ]
};
```

## 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 无数据 | 显示"暂无净值数据"提示 |
| 只有一天数据 | 显示单点，不绘制曲线 |
| 无基准数据 | 只显示策略净值曲线 |

## 技术选型

- **图表库**: ReactECharts (echarts-for-react)，项目已有依赖
- **参考实现**: `StrategyDetail.tsx` 中的权益曲线图表

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/src/components/NetValueChart.tsx` | 新增 | 净值曲线图表组件 |
| `frontend/src/pages/SandboxDetail.tsx` | 修改 | 集成 NetValueChart 组件 |
