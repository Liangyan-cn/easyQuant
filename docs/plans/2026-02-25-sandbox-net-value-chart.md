# 沙盒净值曲线图表实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在沙盒账户详情页添加净值曲线图表，展示账户净值随时间变化趋势并与基准对比

**Architecture:** 创建 NetValueChart 组件，使用 ReactECharts 绘制净值曲线和基准对比线，集成到 SandboxDetail.tsx 的统计卡片下方

**Tech Stack:** React, TypeScript, ReactECharts (echarts-for-react), Ant Design

---

## Task 1: 创建 NetValueChart 组件

**Files:**
- Create: `frontend/src/components/NetValueChart.tsx`

**Step 1: 创建组件文件**

```typescript
import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Empty } from 'antd';
import type { SandboxDailyValue } from '@/types/sandbox';

interface NetValueChartProps {
  dailyValues: SandboxDailyValue[];
  initialCapital: number;
}

const NetValueChart: React.FC<NetValueChartProps> = ({ dailyValues, initialCapital }) => {
  const chartOption = useMemo(() => {
    if (!dailyValues || dailyValues.length === 0) {
      return null;
    }

    const dates = dailyValues.map(d => d.date.split('T')[0]);
    const netValues = dailyValues.map(d => d.total_value / initialCapital);
    const hasBenchmark = dailyValues.some(d => d.benchmark_return !== null && d.benchmark_return !== undefined);
    const benchmarkValues = hasBenchmark
      ? dailyValues.map(d => 1 + (d.benchmark_return || 0))
      : [];

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: { name: string; value: number; seriesName: string; color: string }[]) => {
          const date = params[0]?.name || '';
          const lines = params.map(p => {
            const returnRate = ((p.value - 1) * 100).toFixed(2);
            return `<span style="color:${p.color}">●</span> ${p.seriesName}: ${p.value.toFixed(4)} (${returnRate}%)`;
          });
          return `${date}<br/>${lines.join('<br/>')}`;
        },
      },
      legend: {
        data: hasBenchmark ? ['策略净值', '基准(沪深300)'] : ['策略净值'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '12%',
        top: '8%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => value.toFixed(2),
        },
      },
      series: [
        {
          name: '策略净值',
          type: 'line',
          smooth: true,
          data: netValues,
          lineStyle: { color: '#1890ff', width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
              ],
            },
          },
        },
        ...(hasBenchmark
          ? [
              {
                name: '基准(沪深300)',
                type: 'line',
                smooth: true,
                data: benchmarkValues,
                lineStyle: { color: '#faad14', width: 2, type: 'dashed' as const },
              },
            ]
          : []),
      ],
    };
  }, [dailyValues, initialCapital]);

  if (!dailyValues || dailyValues.length === 0) {
    return (
      <Card title="净值曲线" style={{ marginTop: 24 }}>
        <Empty description="暂无净值数据" />
      </Card>
    );
  }

  return (
    <Card title="净值曲线" style={{ marginTop: 24 }}>
      <ReactECharts option={chartOption!} style={{ height: 300 }} />
    </Card>
  );
};

export default NetValueChart;
```

**Step 2: 验证组件创建成功**

Run: `cd frontend && npm run lint -- --max-warnings=0 src/components/NetValueChart.tsx`
Expected: 无 lint 错误

**Step 3: Commit**

```bash
git add frontend/src/components/NetValueChart.tsx
git commit -m "feat(sandbox): add NetValueChart component"
```

---

## Task 2: 集成到 SandboxDetail 页面

**Files:**
- Modify: `frontend/src/pages/SandboxDetail.tsx`

**Step 1: 添加 import**

在文件顶部添加导入：

```typescript
import NetValueChart from '@/components/NetValueChart';
```

**Step 2: 在统计卡片后添加图表组件**

在 `<Descriptions>` 组件之后、`</Card>` 之前添加：

```typescript
        <NetValueChart
          dailyValues={daily_values}
          initialCapital={account.initial_capital}
        />
```

位置：在 `<Descriptions style={{ marginTop: 24 }} column={2}>` 之后

**Step 3: 验证集成成功**

Run: `cd frontend && npm run lint -- --max-warnings=0 src/pages/SandboxDetail.tsx`
Expected: 无 lint 错误

**Step 4: 启动开发服务器验证**

Run: `cd frontend && npm run dev`
Expected: 访问沙盒详情页，在统计卡片下方看到净值曲线图表

**Step 5: Commit**

```bash
git add frontend/src/pages/SandboxDetail.tsx
git commit -m "feat(sandbox): integrate NetValueChart into SandboxDetail page"
```

---

## Task 3: 验证和测试

**Step 1: 手动测试**

1. 访问 http://localhost:5173/sandbox
2. 点击任意沙盒账户进入详情页
3. 验证净值曲线图表显示在统计卡片下方
4. 验证 Tooltip 显示日期、净值和收益率
5. 验证无数据时显示"暂无净值数据"

**Step 2: 最终 Commit**

```bash
git push
```

---

## 文件变更总结

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/src/components/NetValueChart.tsx` | 新增 | 净值曲线图表组件 |
| `frontend/src/pages/SandboxDetail.tsx` | 修改 | 集成 NetValueChart 组件 |
