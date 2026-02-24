import { useState, useEffect, useCallback } from 'react';
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
  Tabs,
  Popconfirm,
  Input,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { sandboxApi } from '@/api/sandbox';
import { strategyApi } from '@/api/strategy';
import type {
  SandboxAccountDetail,
  SandboxPosition,
  SandboxTransaction,
  SandboxDeployment,
  SandboxStatus,
  DeploymentStatus,
  TransactionType,
} from '@/types/sandbox';
import {
  SANDBOX_STATUS_LABELS,
  DEPLOYMENT_STATUS_LABELS,
  TRANSACTION_TYPE_LABELS,
} from '@/types/sandbox';
import type { Strategy } from '@/types/strategy';

const { Title, Text } = Typography;

const SandboxDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [accountDetail, setAccountDetail] = useState<SandboxAccountDetail | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [depositModalVisible, setDepositModalVisible] = useState(false);
  const [resetModalVisible, setResetModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deployForm] = Form.useForm();
  const [depositForm] = Form.useForm();
  const [resetForm] = Form.useForm();

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [accountRes, strategiesRes] = await Promise.all([
        sandboxApi.getAccount(Number(id)),
        strategyApi.getStrategyList({ size: 100 }),
      ]);
      setAccountDetail(accountRes.data);
      setStrategies(strategiesRes.data.items);
    } catch {
      message.error('获取账户详情失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getStatusColor = (status: SandboxStatus) => {
    const colors: Record<SandboxStatus, string> = {
      active: 'green',
      paused: 'orange',
      stopped: 'default',
    };
    return colors[status];
  };

  const getDeploymentStatusColor = (status: DeploymentStatus) => {
    const colors: Record<DeploymentStatus, string> = {
      pending: 'default',
      running: 'processing',
      paused: 'orange',
      completed: 'success',
      failed: 'error',
    };
    return colors[status];
  };

  const getTransactionTypeColor = (type: TransactionType) => {
    const colors: Record<TransactionType, string> = {
      deposit: 'green',
      withdraw: 'red',
      buy: 'blue',
      sell: 'orange',
      dividend: 'purple',
      fee: 'default',
    };
    return colors[type];
  };

  const formatCurrency = (value: number) => {
    return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const handleCreateDeployment = async () => {
    try {
      const values = await deployForm.validateFields();
      setSubmitting(true);
      await sandboxApi.createDeployment(Number(id), {
        strategy_id: values.strategy_id,
        name: values.name,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
        stock_pool: values.stock_pool,
        allocation_ratio: values.allocation_ratio || 1.0,
      });
      message.success('策略部署创建成功');
      setDeployModalVisible(false);
      deployForm.resetFields();
      fetchData();
    } catch {
      message.error('创建策略部署失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunDeployment = async (deploymentId: number) => {
    try {
      await sandboxApi.runDeployment(deploymentId);
      message.success('策略运行成功');
      fetchData();
    } catch {
      message.error('策略运行失败');
    }
  };

  const handleStopDeployment = async (deploymentId: number) => {
    try {
      await sandboxApi.stopDeployment(deploymentId);
      message.success('策略已暂停');
      fetchData();
    } catch {
      message.error('暂停失败');
    }
  };

  const handleStartDeployment = async (deploymentId: number) => {
    try {
      await sandboxApi.startDeployment(deploymentId);
      message.success('策略已恢复');
      fetchData();
    } catch {
      message.error('恢复失败');
    }
  };

  const handleDeposit = async () => {
    try {
      const values = await depositForm.validateFields();
      setSubmitting(true);
      await sandboxApi.deposit(Number(id), {
        amount: values.amount,
        description: values.description,
      });
      message.success('入金成功');
      setDepositModalVisible(false);
      depositForm.resetFields();
      fetchData();
    } catch {
      message.error('入金失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = async () => {
    try {
      const values = await resetForm.validateFields();
      setSubmitting(true);
      await sandboxApi.resetAccount(Number(id), {
        initial_capital: values.initial_capital,
      });
      message.success('账户重置成功');
      setResetModalVisible(false);
      resetForm.resetFields();
      fetchData();
    } catch {
      message.error('账户重置失败');
    } finally {
      setSubmitting(false);
    }
  };

  const positionColumns: ColumnsType<SandboxPosition> = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: '成本价',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      width: 100,
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 100,
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      key: 'market_value',
      width: 120,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '浮动盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      width: 120,
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322' }}>
          {value >= 0 ? '+' : ''}{formatCurrency(value)}
        </span>
      ),
    },
    {
      title: '已实现盈亏',
      dataIndex: 'realized_pnl',
      key: 'realized_pnl',
      width: 120,
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322' }}>
          {value >= 0 ? '+' : ''}{formatCurrency(value)}
        </span>
      ),
    },
  ];

  const transactionColumns: ColumnsType<SandboxTransaction> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 80,
      render: (type: TransactionType) => (
        <Tag color={getTransactionTypeColor(type)}>{TRANSACTION_TYPE_LABELS[type]}</Tag>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (value: number) => value?.toLocaleString() || '-',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (value: number) => value ? `¥${value.toFixed(2)}` : '-',
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '手续费',
      dataIndex: 'commission',
      key: 'commission',
      width: 80,
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
  ];

  const deploymentColumns: ColumnsType<SandboxDeployment> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: DeploymentStatus) => (
        <Tag color={getDeploymentStatusColor(status)}>{DEPLOYMENT_STATUS_LABELS[status]}</Tag>
      ),
    },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 110,
    },
    {
      title: '结束日期',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 110,
      render: (text: string) => text || '持续运行',
    },
    {
      title: '资金比例',
      dataIndex: 'allocation_ratio',
      key: 'allocation_ratio',
      width: 100,
      render: (value: number) => `${(value * 100).toFixed(0)}%`,
    },
    {
      title: '最后运行',
      dataIndex: 'last_run_date',
      key: 'last_run_date',
      width: 110,
      render: (text: string) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.status === 'pending' && (
            <Popconfirm
              title="确定运行此策略？"
              onConfirm={() => handleRunDeployment(record.id)}
            >
              <Button type="link" size="small" icon={<PlayCircleOutlined />}>
                运行
              </Button>
            </Popconfirm>
          )}
          {record.status === 'running' && (
            <>
              <Popconfirm
                title="确定运行此策略？"
                onConfirm={() => handleRunDeployment(record.id)}
              >
                <Button type="link" size="small" icon={<PlayCircleOutlined />}>
                  运行
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定暂停此策略？"
                onConfirm={() => handleStopDeployment(record.id)}
              >
                <Button type="link" size="small" danger icon={<PauseCircleOutlined />}>
                  暂停
                </Button>
              </Popconfirm>
            </>
          )}
          {record.status === 'paused' && (
            <Popconfirm
              title="确定恢复此策略？"
              onConfirm={() => handleStartDeployment(record.id)}
            >
              <Button type="link" size="small" icon={<PlayCircleOutlined />}>
                恢复
              </Button>
            </Popconfirm>
          )}
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

  if (!accountDetail) {
    return <Empty description="账户不存在" />;
  }

  const { account, positions, recent_transactions, deployments, daily_values } = accountDetail;
  const totalReturn = account.initial_capital > 0
    ? (account.total_value - account.initial_capital) / account.initial_capital
    : 0;
  const positionValue = account.total_value - account.current_cash;

  const latestDailyValue = daily_values.length > 0 ? daily_values[daily_values.length - 1] : null;

  const tabItems = [
    {
      key: 'positions',
      label: `持仓 (${positions.length})`,
      children: positions.length > 0 ? (
        <Table
          columns={positionColumns}
          dataSource={positions}
          rowKey="id"
          pagination={false}
          scroll={{ x: 960 }}
        />
      ) : (
        <Empty description="暂无持仓" />
      ),
    },
    {
      key: 'transactions',
      label: `交易记录 (${recent_transactions.length})`,
      children: recent_transactions.length > 0 ? (
        <Table
          columns={transactionColumns}
          dataSource={recent_transactions}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      ) : (
        <Empty description="暂无交易记录" />
      ),
    },
    {
      key: 'deployments',
      label: `策略部署 (${deployments.length})`,
      children: (
        <>
          <div style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setDeployModalVisible(true)}
            >
              部署策略
            </Button>
          </div>
          {deployments.length > 0 ? (
            <Table
              columns={deploymentColumns}
              dataSource={deployments}
              rowKey="id"
              pagination={false}
            />
          ) : (
            <Empty description="暂无策略部署" />
          )}
        </>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/sandbox')}>
          返回列表
        </Button>
      </Space>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={4} style={{ marginBottom: 8 }}>
              {account.name}
              <Tag color={getStatusColor(account.status)} style={{ marginLeft: 8 }}>
                {SANDBOX_STATUS_LABELS[account.status]}
              </Tag>
            </Title>
            <Text type="secondary">{account.description || '暂无描述'}</Text>
          </div>
          <Space>
            <Button icon={<DollarOutlined />} onClick={() => setDepositModalVisible(true)}>
              入金
            </Button>
            <Popconfirm
              title="确定重置账户？"
              description="重置后所有持仓和交易记录将被清除"
              onConfirm={() => {
                resetForm.setFieldsValue({ initial_capital: account.initial_capital });
                setResetModalVisible(true);
              }}
            >
              <Button icon={<ReloadOutlined />} danger>
                重置
              </Button>
            </Popconfirm>
          </Space>
        </div>

        <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="总资产"
              value={account.total_value}
              precision={2}
              prefix="¥"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="可用现金"
              value={account.current_cash}
              precision={2}
              prefix="¥"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="持仓市值"
              value={positionValue}
              precision={2}
              prefix="¥"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="初始资金"
              value={account.initial_capital}
              precision={2}
              prefix="¥"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="累计收益"
              value={account.total_value - account.initial_capital}
              precision={2}
              prefix="¥"
              valueStyle={{ color: totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="收益率"
              value={totalReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          {latestDailyValue && (
            <>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="今日收益率"
                  value={(latestDailyValue.daily_return || 0) * 100}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (latestDailyValue.daily_return || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="累计收益率"
                  value={(latestDailyValue.cumulative_return || 0) * 100}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (latestDailyValue.cumulative_return || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
            </>
          )}
        </Row>

        <Descriptions style={{ marginTop: 24 }} column={2}>
          <Descriptions.Item label="创建时间">
            {dayjs(account.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(account.updated_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card>
        <Tabs items={tabItems} />
      </Card>

      <Modal
        title="部署策略"
        open={deployModalVisible}
        onOk={handleCreateDeployment}
        onCancel={() => setDeployModalVisible(false)}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={deployForm} layout="vertical">
          <Form.Item
            name="strategy_id"
            label="选择策略"
            rules={[{ required: true, message: '请选择策略' }]}
          >
            <Select
              placeholder="请选择要部署的策略"
              options={strategies.map((s) => ({ value: s.id, label: `${s.name} (${s.code})` }))}
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="部署名称"
            rules={[{ required: true, message: '请输入部署名称' }]}
          >
            <Input placeholder="请输入部署名称" maxLength={100} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="start_date"
                label="开始日期"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="结束日期">
                <DatePicker style={{ width: '100%' }} placeholder="留空表示持续运行" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="allocation_ratio" label="资金比例" initialValue={1.0}>
            <InputNumber<number>
              style={{ width: '100%' }}
              min={0}
              max={1}
              step={0.1}
              formatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
              parser={(value) => Number(value?.replace('%', '') || 0) / 100}
            />
          </Form.Item>
          <Form.Item name="stock_pool" label="股票池">
            <Select
              mode="tags"
              placeholder="输入股票代码，如 000001.SZ（留空使用策略默认股票池）"
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="入金"
        open={depositModalVisible}
        onOk={handleDeposit}
        onCancel={() => setDepositModalVisible(false)}
        confirmLoading={submitting}
        width={400}
      >
        <Form form={depositForm} layout="vertical">
          <Form.Item
            name="amount"
            label="入金金额"
            rules={[{ required: true, message: '请输入入金金额' }]}
          >
            <InputNumber<number>
              style={{ width: '100%' }}
              min={1}
              max={100000000}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => Number(value?.replace(/¥\s?|(,*)/g, '') || 0)}
              placeholder="请输入入金金额"
            />
          </Form.Item>
          <Form.Item name="description" label="备注">
            <Input.TextArea rows={2} placeholder="请输入备注（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="重置账户"
        open={resetModalVisible}
        onOk={handleReset}
        onCancel={() => setResetModalVisible(false)}
        confirmLoading={submitting}
        width={400}
      >
        <Form form={resetForm} layout="vertical">
          <Form.Item
            name="initial_capital"
            label="初始资金"
            rules={[{ required: true, message: '请输入初始资金' }]}
          >
            <InputNumber<number>
              style={{ width: '100%' }}
              min={10000}
              max={100000000}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => Number(value?.replace(/¥\s?|(,*)/g, '') || 0)}
              placeholder="请输入初始资金"
            />
          </Form.Item>
          <Text type="warning">
            警告：重置账户将清除所有持仓、交易记录和策略部署数据！
          </Text>
        </Form>
      </Modal>
    </div>
  );
};

export default SandboxDetail;
