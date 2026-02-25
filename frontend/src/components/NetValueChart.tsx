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
