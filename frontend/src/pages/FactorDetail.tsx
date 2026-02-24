import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Typography, message, DatePicker, Spin, Statistic, Row, Col, Tag, Checkbox } from 'antd';
import { ArrowLeftOutlined, ExperimentOutlined, ReloadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import axios from 'axios';
import { factorApi } from '@/api/factor';
import type { Factor, FactorAnalyzeResponse, FactorEvaluation } from '@/types/factor';
import { FACTOR_CATEGORY_LABELS } from '@/types/factor';

const { Text } = Typography;
const { RangePicker } = DatePicker;

interface EvaluationData {
  evaluation: FactorEvaluation;
  ic_series: Array<{ date: string; ic: number }>;
  group_returns: Array<{ group: number; return_value: number; stock_count: number }>;
}

const FactorDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [factor, setFactor] = useState<Factor | null>(null);
  const [evaluationData, setEvaluationData] = useState<EvaluationData | null>(null);
  const [latestEvaluation, setLatestEvaluation] = useState<FactorEvaluation | null>(null);
  const [forceRecalculate, setForceRecalculate] = useState(false);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(1, 'year'),
    dayjs(),
  ]);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setLoading(true);
      try {
        const [factorRes, latestEvalRes] = await Promise.all([
          factorApi.getFactor(parseInt(id), { signal: abortControllerRef.current.signal }),
          factorApi.getLatestEvaluation(parseInt(id), { signal: abortControllerRef.current.signal }),
        ]);
        setFactor(factorRes.data);
        if (latestEvalRes.data) {
          setLatestEvaluation(latestEvalRes.data);
        }
      } catch (error) {
        if (!axios.isCancel(error)) {
          message.error('获取因子详情失败');
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
  }, [id]);

  const handleAnalyze = async () => {
    if (!factor || !dateRange) return;

    setAnalyzing(true);
    try {
      const response = await factorApi.analyzeFactor({
        factor_id: factor.id,
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        force_recalculate: forceRecalculate,
      });
      const data: FactorAnalyzeResponse = response.data;
      setEvaluationData({
        evaluation: data.evaluation,
        ic_series: data.ic_series,
        group_returns: data.group_returns,
      });
      setLatestEvaluation(data.evaluation);
      message.success(`分析完成: 计算了 ${data.calculated_count} 条因子值`);
    } catch (error: unknown) {
      console.error('分析错误:', error);
      const axiosError = error as { response?: { data?: { detail?: string } }, message?: string, code?: string };
      const detail = axiosError?.response?.data?.detail;
      if (axiosError?.code === 'ECONNABORTED' || axiosError?.message?.includes('timeout')) {
        message.error('分析超时，请缩短日期范围后重试');
      } else {
        message.error('分析失败: ' + (detail || axiosError?.message || '未知错误'));
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const getICChartOption = () => {
    if (!evaluationData?.ic_series?.length) return {};

    return {
      title: { text: 'IC 时序图', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: evaluationData.ic_series.map((item) => item.date),
      },
      yAxis: { type: 'value', name: 'IC' },
      series: [
        {
          name: 'IC',
          type: 'bar',
          data: evaluationData.ic_series.map((item) => item.ic.toFixed(4)),
          itemStyle: {
            color: (params: { value: number }) => (params.value >= 0 ? '#52c41a' : '#ff4d4f'),
          },
        },
      ],
    };
  };

  const getGroupReturnChartOption = () => {
    if (!evaluationData?.group_returns?.length) return {};

    return {
      title: { text: '分组收益', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: evaluationData.group_returns.map((item) => `第${item.group}组`),
        name: '分组',
      },
      yAxis: { type: 'value', name: '收益率' },
      series: [
        {
          name: '平均收益',
          type: 'bar',
          data: evaluationData.group_returns.map((item) => (item.return_value * 100).toFixed(2)),
          itemStyle: {
            color: (params: { dataIndex: number }) => {
              const colors = ['#ff4d4f', '#faad14', '#d9d9d9', '#52c41a', '#1890ff'];
              return colors[params.dataIndex] || '#1890ff';
            },
          },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!factor) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/factors')}>
          返回列表
        </Button>
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Text type="secondary">因子不存在</Text>
        </div>
      </div>
    );
  }

  const displayEvaluation = evaluationData?.evaluation || latestEvaluation;

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/factors')}>
          返回列表
        </Button>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions title={factor.name} bordered column={2}>
          <Descriptions.Item label="代码">{factor.code}</Descriptions.Item>
          <Descriptions.Item label="分类">
            <Tag color="blue">{FACTOR_CATEGORY_LABELS[factor.category]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag color={factor.is_builtin ? 'green' : 'orange'}>
              {factor.is_builtin ? '内置' : '自定义'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(factor.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {factor.description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="公式" span={2}>
            <code>{factor.formula || '-'}</code>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="因子分析" style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }} wrap>
          <Text>日期范围:</Text>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
          />
          <Checkbox
            checked={forceRecalculate}
            onChange={(e) => setForceRecalculate(e.target.checked)}
          >
            强制重新计算
          </Checkbox>
          <Button
            type="primary"
            icon={analyzing ? <ReloadOutlined spin /> : <ExperimentOutlined />}
            loading={analyzing}
            onClick={handleAnalyze}
          >
            {analyzing ? '分析中...' : '开始分析'}
          </Button>
        </Space>

        {latestEvaluation && !evaluationData && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Text type="secondary">
              最近评估: {dayjs(latestEvaluation.created_at).format('YYYY-MM-DD HH:mm')} |
              时间范围: {dayjs(latestEvaluation.start_date).format('YYYY-MM-DD')} ~ {dayjs(latestEvaluation.end_date).format('YYYY-MM-DD')}
            </Text>
          </div>
        )}

        {displayEvaluation && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="IC 均值"
                    value={displayEvaluation.ic_mean?.toFixed(4) || '-'}
                    valueStyle={{
                      color: (displayEvaluation.ic_mean || 0) > 0 ? '#3f8600' : '#cf1322',
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="IC 标准差"
                    value={displayEvaluation.ic_std?.toFixed(4) || '-'}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="IR (信息比率)"
                    value={displayEvaluation.ir?.toFixed(4) || '-'}
                    valueStyle={{
                      color: (displayEvaluation.ir || 0) > 0.5 ? '#3f8600' : undefined,
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="IC 正比例"
                    value={
                      displayEvaluation.ic_positive_ratio
                        ? `${(displayEvaluation.ic_positive_ratio * 100).toFixed(1)}%`
                        : '-'
                    }
                  />
                </Card>
              </Col>
            </Row>

            {evaluationData && (
              <Row gutter={16}>
                <Col span={12}>
                  {evaluationData.ic_series?.length > 0 && (
                    <ReactECharts option={getICChartOption()} style={{ height: 300 }} />
                  )}
                </Col>
                <Col span={12}>
                  {evaluationData.group_returns?.length > 0 && (
                    <ReactECharts option={getGroupReturnChartOption()} style={{ height: 300 }} />
                  )}
                </Col>
              </Row>
            )}
          </>
        )}

        {!displayEvaluation && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Text type="secondary">暂无评估数据，请点击"开始分析"按钮</Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default FactorDetail;
