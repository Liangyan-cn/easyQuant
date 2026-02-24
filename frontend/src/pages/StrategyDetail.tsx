import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Typography,
  Spin,
  message,
  Table,
  Statistic,
  Row,
  Col,
  Empty,
  Modal,
  Form,
  DatePicker,
  InputNumber,
  Select,
  Alert,
  Tooltip,
} from 'antd';
import { ArrowLeftOutlined, PlayCircleOutlined, LineChartOutlined, DeleteOutlined, ReloadOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import ReactECharts from 'echarts-for-react';
import { strategyApi } from '@/api/strategy';
import type { Strategy, Backtest, BacktestStatus, BacktestResult, EquityCurvePoint } from '@/types/strategy';
import { STRATEGY_TYPE_LABELS, STRATEGY_STATUS_LABELS, BACKTEST_STATUS_LABELS } from '@/types/strategy';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const getStrategyTypeDescription = (type: string): string => {
  const descriptions: Record<string, string> = {
    momentum: '动量策略基于"强者恒强"的理念，买入近期涨幅较大的股票。适合趋势明显的市场，但在震荡市可能表现不佳。',
    mean_reversion: '均值回归策略认为价格会向均值回归，在价格偏离均值时反向操作。适合震荡市，但在趋势市可能产生较大回撤。',
    trend_following: '趋势跟踪策略顺势而为，在趋势形成时入场，趋势结束时离场。常用均线、突破等信号判断趋势。',
    factor_based: '因子策略基于量化因子选股，如价值因子(PE/PB)、质量因子(ROE)等。通过因子打分选择股票组合。',
    custom: '自定义策略，可根据自己的交易逻辑编写策略代码。',
  };
  return descriptions[type] || '暂无说明';
};

const StrategyDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [backtestModalVisible, setBacktestModalVisible] = useState(false);
  const [runningBacktest, setRunningBacktest] = useState(false);
  const [selectedBacktest, setSelectedBacktest] = useState<{ backtest: Backtest; result?: BacktestResult; equityCurve?: EquityCurvePoint[] } | null>(null);
  const [resultModalVisible, setResultModalVisible] = useState(false);
  const [rerunningBacktestId, setRerunningBacktestId] = useState<number | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [strategyRes, backtestsRes] = await Promise.all([
        strategyApi.getStrategy(Number(id)),
        strategyApi.getStrategyBacktests(Number(id), 10),
      ]);
      setStrategy(strategyRes.data);
      setBacktests(backtestsRes.data.items);
    } catch {
      message.error('获取策略详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleCreateBacktest = async () => {
    try {
      const values = await form.validateFields();
      const [startDate, endDate] = values.dateRange;

      const backtestData = {
        strategy_id: Number(id),
        name: values.name || `回测 ${dayjs().format('YYYY-MM-DD HH:mm')}`,
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
        initial_capital: values.initial_capital || 1000000,
        commission_rate: values.commission_rate || 0.0003,
        slippage: values.slippage || 0.001,
        stock_pool: values.stock_pool || ['000001.SZ', '000002.SZ', '600000.SH'],
      };

      const response = await strategyApi.createBacktest(backtestData);
      message.success('回测任务创建成功');
      setBacktestModalVisible(false);
      form.resetFields();

      setRunningBacktest(true);
      try {
        const runResponse = await strategyApi.runBacktest(response.data.id);
        message.success(`回测完成！总收益: ${((runResponse.data.result?.total_return || 0) * 100).toFixed(2)}%`);
      } catch {
        message.error('回测执行失败');
      } finally {
        setRunningBacktest(false);
      }

      fetchData();
    } catch {
      message.error('创建回测失败');
    }
  };

  const handleViewResult = async (backtest: Backtest) => {
    try {
      const response = await strategyApi.getBacktest(backtest.id);
      setSelectedBacktest({
        backtest: response.data.backtest,
        result: response.data.result || undefined,
        equityCurve: response.data.equity_curve || undefined,
      });
      setResultModalVisible(true);
    } catch {
      message.error('获取回测结果失败');
    }
  };

  const handleDeleteBacktest = async (backtestId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个回测记录吗？此操作不可恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await strategyApi.deleteBacktest(backtestId);
          message.success('删除成功');
          fetchData();
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  const handleRerunBacktest = async (backtestId: number) => {
    setRerunningBacktestId(backtestId);
    try {
      const runResponse = await strategyApi.runBacktest(backtestId);
      message.success(`回测完成！总收益: ${((runResponse.data.result?.total_return || 0) * 100).toFixed(2)}%`);
      fetchData();
    } catch {
      message.error('回测执行失败');
    } finally {
      setRerunningBacktestId(null);
    }
  };

  const getStatusColor = (status: BacktestStatus) => {
    const colors: Record<BacktestStatus, string> = {
      pending: 'default',
      running: 'processing',
      completed: 'success',
      failed: 'error',
    };
    return colors[status];
  };

  const backtestColumns: ColumnsType<Backtest> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => name || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: BacktestStatus) => (
        <Tag color={getStatusColor(status)}>{BACKTEST_STATUS_LABELS[status]}</Tag>
      ),
    },
    {
      title: '回测区间',
      key: 'period',
      render: (_, record) => (
        <Text>{record.start_date.split('T')[0]} ~ {record.end_date.split('T')[0]}</Text>
      ),
    },
    {
      title: '初始资金',
      dataIndex: 'initial_capital',
      key: 'initial_capital',
      render: (value: number) => `¥${value.toLocaleString()}`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value: string) => value.split('T')[0],
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<LineChartOutlined />}
              onClick={() => handleViewResult(record)}
            >
              查看结果
            </Button>
          )}
          {record.status === 'failed' && (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              loading={rerunningBacktestId === record.id}
              onClick={() => handleRerunBacktest(record.id)}
            >
              重新运行
            </Button>
          )}
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteBacktest(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!strategy) {
    return <Empty description="策略不存在" />;
  }

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/strategies')}>
          返回列表
        </Button>
      </Space>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={4} style={{ marginBottom: 8 }}>
              {strategy.name}
              {strategy.is_builtin && (
                <Tag color="green" style={{ marginLeft: 8 }}>内置</Tag>
              )}
            </Title>
            <Text type="secondary">{strategy.code}</Text>
          </div>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => setBacktestModalVisible(true)}
            loading={runningBacktest}
          >
            运行回测
          </Button>
        </div>

        {strategy.is_builtin && (
          <Alert
            message="内置策略说明"
            description={getStrategyTypeDescription(strategy.strategy_type)}
            type="info"
            showIcon
            style={{ marginTop: 16, marginBottom: 16 }}
          />
        )}

        <Descriptions style={{ marginTop: 24 }} column={2}>
          <Descriptions.Item label="策略类型">
            <Tag color="blue">{STRATEGY_TYPE_LABELS[strategy.strategy_type]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {strategy.description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="策略逻辑" span={2}>
            <Text code>{strategy.logic || '-'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="参数配置" span={2}>
            <Text code>{strategy.parameters ? JSON.stringify(strategy.parameters, null, 2) : '-'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {strategy.created_at.split('T')[0]}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {strategy.updated_at.split('T')[0]}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="回测历史">
        {backtests.length > 0 ? (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic title="回测次数" value={backtests.length} />
              </Col>
              <Col span={6}>
                <Statistic
                  title="成功次数"
                  value={backtests.filter((b) => b.status === 'completed').length}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="失败次数"
                  value={backtests.filter((b) => b.status === 'failed').length}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="运行中"
                  value={backtests.filter((b) => b.status === 'running').length}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>
            <Table
              columns={backtestColumns}
              dataSource={backtests}
              rowKey="id"
              pagination={false}
            />
          </>
        ) : (
          <Empty description="暂无回测记录" />
        )}
      </Card>

      <Modal
        title="创建回测"
        open={backtestModalVisible}
        onOk={handleCreateBacktest}
        onCancel={() => setBacktestModalVisible(false)}
        confirmLoading={runningBacktest}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="dateRange"
            label="回测区间"
            rules={[{ required: true, message: '请选择回测区间' }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="initial_capital" label="初始资金" initialValue={1000000}>
            <InputNumber
              style={{ width: '100%' }}
              min={10000}
              max={100000000}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="commission_rate" label="手续费率" initialValue={0.0003}>
                <InputNumber style={{ width: '100%' }} min={0} max={0.01} step={0.0001} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="slippage" label="滑点" initialValue={0.001}>
                <InputNumber style={{ width: '100%' }} min={0} max={0.05} step={0.001} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="stock_pool" label="股票池">
            <Select
              mode="tags"
              placeholder="输入股票代码，如 000001.SZ"
              defaultValue={['000001.SZ', '000002.SZ', '600000.SH']}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="回测结果"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedBacktest?.result ? (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic
                  title="总收益"
                  value={(selectedBacktest.result.total_return || 0) * 100}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (selectedBacktest.result.total_return || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="年化收益"
                  value={(selectedBacktest.result.annual_return || 0) * 100}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (selectedBacktest.result.annual_return || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="最大回撤"
                  value={(selectedBacktest.result.max_drawdown || 0) * 100}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="夏普比率"
                  value={selectedBacktest.result.sharpe_ratio || 0}
                  precision={2}
                />
              </Col>
            </Row>
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Statistic
                  title="波动率"
                  value={(selectedBacktest.result.volatility || 0) * 100}
                  precision={2}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="胜率"
                  value={(selectedBacktest.result.win_rate || 0) * 100}
                  precision={2}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="盈亏比"
                  value={selectedBacktest.result.profit_loss_ratio || 0}
                  precision={2}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="交易次数"
                  value={selectedBacktest.result.total_trades || 0}
                />
              </Col>
            </Row>
            {selectedBacktest.equityCurve && selectedBacktest.equityCurve.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <Title level={5}>权益曲线</Title>
                <ReactECharts
                  option={{
                    tooltip: {
                      trigger: 'axis',
                      formatter: (params: { name: string; value: number; seriesName: string }[]) => {
                        const date = params[0]?.name || '';
                        const lines = params.map(p => `${p.seriesName}: ¥${p.value.toLocaleString()}`);
                        return `${date}<br/>${lines.join('<br/>')}`;
                      },
                    },
                    legend: {
                      data: ['策略权益', '基准'],
                      bottom: 0,
                    },
                    grid: {
                      left: '3%',
                      right: '4%',
                      bottom: '12%',
                      top: '3%',
                      containLabel: true,
                    },
                    xAxis: {
                      type: 'category',
                      boundaryGap: false,
                      data: selectedBacktest.equityCurve.map(p => p.date.split('T')[0]),
                    },
                    yAxis: {
                      type: 'value',
                      axisLabel: {
                        formatter: (value: number) => `¥${(value / 10000).toFixed(0)}万`,
                      },
                    },
                    series: [
                      {
                        name: '策略权益',
                        type: 'line',
                        smooth: true,
                        data: selectedBacktest.equityCurve.map(p => p.equity),
                        lineStyle: { color: '#1890ff' },
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
                      ...(selectedBacktest.equityCurve.some(p => p.benchmark !== undefined)
                        ? [
                          {
                            name: '基准',
                            type: 'line',
                            smooth: true,
                            data: selectedBacktest.equityCurve.map(p => p.benchmark),
                            lineStyle: { color: '#faad14' },
                          },
                        ]
                        : []),
                    ],
                  }}
                  style={{ height: 300 }}
                />
              </div>
            )}
          </div>
        ) : (
          <Empty description="暂无结果数据" />
        )}
      </Modal>
    </div>
  );
};

export default StrategyDetail;
