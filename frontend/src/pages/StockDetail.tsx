import { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Segmented, Spin, Typography, Button, message, Space } from 'antd';
import { ArrowLeftOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';
import { stockApi } from '@/api/stock';
import type { StockHistoryResponse, OHLCVItem } from '@/types/stock';

const { Title } = Typography;

type PeriodType = 'daily' | 'weekly' | 'monthly';

const periodOptions = [
  { label: '日线', value: 'daily' },
  { label: '周线', value: 'weekly' },
  { label: '月线', value: 'monthly' },
];

const StockDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<PeriodType>('daily');
  const [stockData, setStockData] = useState<StockHistoryResponse | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!code) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await stockApi.getStockHistory(code, { period }, {
          signal: abortControllerRef.current?.signal,
        });
        setStockData(response.data);
      } catch (error) {
        if (!axios.isCancel(error)) {
          message.error('获取股票数据失败');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [code, period]);

  const chartOption = useMemo(() => {
    if (!stockData?.items?.length) return {};

    const data = stockData.items;
    const dates = data.map((item: OHLCVItem) => item.date);
    const ohlcData = data.map((item: OHLCVItem) => [item.open, item.close, item.low, item.high]);
    const volumes = data.map((item: OHLCVItem, index: number) => {
      const isUp = index === 0 ? item.close >= item.open : item.close >= data[index - 1].close;
      return {
        value: item.volume,
        itemStyle: { color: isUp ? '#f5222d' : '#52c41a' },
      };
    });

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: ['K线', '成交量'],
        top: 10,
      },
      grid: [
        { left: '10%', right: '8%', top: 60, height: '50%' },
        { left: '10%', right: '8%', top: '70%', height: '16%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          gridIndex: 0,
          axisLine: { onZero: false },
          splitLine: { show: false },
          axisLabel: { show: false },
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
          axisLine: { onZero: false },
          splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          type: 'value',
          gridIndex: 0,
          scale: true,
          splitArea: { show: true },
        },
        {
          type: 'value',
          gridIndex: 1,
          scale: true,
          splitNumber: 2,
          axisLabel: {
            formatter: (value: number) => {
              if (value >= 100000000) return `${(value / 100000000).toFixed(1)}亿`;
              if (value >= 10000) return `${(value / 10000).toFixed(0)}万`;
              return value.toString();
            },
          },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: 10,
          start: 50,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlcData,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#f5222d',
            color0: '#52c41a',
            borderColor: '#f5222d',
            borderColor0: '#52c41a',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          data: volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };
  }, [stockData]);

  const latestData = stockData?.items?.[stockData.items.length - 1];
  const prevData = stockData?.items?.[stockData.items.length - 2];
  const change = latestData && prevData ? latestData.close - prevData.close : 0;
  const changePercent = latestData && prevData ? (change / prevData.close) * 100 : 0;

  return (
    <Spin spinning={loading}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/stocks')}>
            返回列表
          </Button>
        </Space>

        <Card>
          <Title level={3}>
            {stockData?.code || code}
            {latestData && (
              <span
                style={{
                  marginLeft: 16,
                  fontSize: 24,
                  color: change >= 0 ? '#f5222d' : '#52c41a',
                }}
              >
                {latestData.close.toFixed(2)}
                {change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                <span style={{ fontSize: 16, marginLeft: 8 }}>
                  {change >= 0 ? '+' : ''}{change.toFixed(2)} ({change >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                </span>
              </span>
            )}
          </Title>

          {latestData && (
            <Descriptions column={{ xs: 2, sm: 3, md: 4 }} size="small">
              <Descriptions.Item label="开盘">{latestData.open.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="最高">{latestData.high.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="最低">{latestData.low.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="收盘">{latestData.close.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="成交量">
                {latestData.volume >= 100000000
                  ? `${(latestData.volume / 100000000).toFixed(2)}亿`
                  : latestData.volume >= 10000
                    ? `${(latestData.volume / 10000).toFixed(2)}万`
                    : latestData.volume}
              </Descriptions.Item>
              {latestData.amount && (
                <Descriptions.Item label="成交额">
                  {latestData.amount >= 100000000
                    ? `${(latestData.amount / 100000000).toFixed(2)}亿`
                    : latestData.amount >= 10000
                      ? `${(latestData.amount / 10000).toFixed(2)}万`
                      : latestData.amount.toFixed(2)}
                </Descriptions.Item>
              )}
            </Descriptions>
          )}
        </Card>

        <Card
          title="K线图"
          extra={
            <Segmented
              options={periodOptions}
              value={period}
              onChange={(value) => setPeriod(value as PeriodType)}
            />
          }
        >
          {stockData?.items?.length ? (
            <ReactECharts option={chartOption} style={{ height: 500 }} />
          ) : (
            <div style={{ height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              暂无数据
            </div>
          )}
        </Card>
      </Space>
    </Spin>
  );
};

export default StockDetail;
