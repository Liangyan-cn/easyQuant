import { useState, useEffect, useCallback, useRef } from 'react';
import { Table, Input, Select, Space, Typography, Button, Tag, Modal, Form, message, Popconfirm, Alert, Tooltip } from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined, LineChartOutlined, CopyOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import axios from 'axios';
import { strategyApi } from '@/api/strategy';
import type { Strategy, StrategyType, StrategyStatus, StrategyListParams, StrategyCreate } from '@/types/strategy';
import { STRATEGY_TYPE_LABELS, STRATEGY_STATUS_LABELS } from '@/types/strategy';

const { Title } = Typography;

const typeOptions = Object.entries(STRATEGY_TYPE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const statusOptions = Object.entries(STRATEGY_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const Strategies: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<StrategyListParams>({
    page: 1,
    size: 20,
    keyword: '',
    strategy_type: undefined,
    status: undefined,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [form] = Form.useForm();
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchStrategies = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await strategyApi.getStrategyList(params, {
        signal: abortControllerRef.current.signal,
      });
      setStrategies(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      if (!axios.isCancel(error)) {
        message.error('获取策略列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchStrategies();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchStrategies]);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams((prev) => ({
      ...prev,
      page: pagination.current || 1,
      size: pagination.pageSize || 20,
    }));
  };

  const handleSearch = (value: string) => {
    setParams((prev) => ({ ...prev, keyword: value, page: 1 }));
  };

  const handleTypeChange = (value: StrategyType | undefined) => {
    setParams((prev) => ({ ...prev, strategy_type: value, page: 1 }));
  };

  const handleStatusChange = (value: StrategyStatus | undefined) => {
    setParams((prev) => ({ ...prev, status: value, page: 1 }));
  };

  const handleCreate = () => {
    setEditingStrategy(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue(strategy);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await strategyApi.deleteStrategy(id);
      message.success('删除成功');
      fetchStrategies();
    } catch {
      message.error('删除失败');
    }
  };

  const handleClone = async (id: number) => {
    try {
      await strategyApi.cloneStrategy(id);
      message.success('复制成功');
      fetchStrategies();
    } catch {
      message.error('复制失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingStrategy) {
        await strategyApi.updateStrategy(editingStrategy.id, values);
        message.success('更新成功');
      } else {
        await strategyApi.createStrategy(values as StrategyCreate);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchStrategies();
    } catch {
      message.error('操作失败');
    }
  };

  const getStatusColor = (status: StrategyStatus) => {
    const colors: Record<StrategyStatus, string> = {
      draft: 'default',
      active: 'green',
      archived: 'orange',
    };
    return colors[status];
  };

  const columns: ColumnsType<Strategy> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '代码',
      dataIndex: 'code',
      key: 'code',
      width: 150,
    },
    {
      title: '类型',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      width: 120,
      render: (type: StrategyType) => (
        <Tag color="blue">{STRATEGY_TYPE_LABELS[type]}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: StrategyStatus) => (
        <Tag color={getStatusColor(status)}>{STRATEGY_STATUS_LABELS[status]}</Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'is_builtin',
      key: 'is_builtin',
      width: 80,
      render: (isBuiltin: boolean) => (
        <Tag color={isBuiltin ? 'green' : 'purple'}>{isBuiltin ? '内置' : '自定义'}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<LineChartOutlined />}
            onClick={() => navigate(`/strategies/${record.id}`)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => handleClone(record.id)}
          >
            复制
          </Button>
          {!record.is_builtin && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定删除此策略？"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>策略管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建策略
        </Button>
      </div>

      {strategies.length === 0 && !loading && (
        <Alert
          message="开始使用策略"
          description={
            <div>
              <p style={{ marginBottom: 8 }}>策略是定义买卖规则的交易逻辑。您可以：</p>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li><strong>使用内置策略</strong>：系统预置的经典策略，可直接运行回测</li>
                <li><strong>复制并修改</strong>：基于内置策略调整参数</li>
                <li><strong>新建自定义策略</strong>：编写自己的交易逻辑</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索策略名称或代码"
          allowClear
          onSearch={handleSearch}
          style={{ width: 250 }}
          prefix={<SearchOutlined />}
        />
        <Select
          placeholder="策略类型"
          allowClear
          style={{ width: 130 }}
          options={typeOptions}
          onChange={handleTypeChange}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={strategies}
        rowKey="id"
        loading={loading}
        pagination={{
          current: params.page,
          pageSize: params.size,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条`,
        }}
        onChange={handleTableChange}
      />

      <Modal
        title={editingStrategy ? '编辑策略' : '新建策略'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="请输入策略名称" />
          </Form.Item>
          <Form.Item
            name="code"
            label="代码"
            rules={[{ required: true, message: '请输入策略代码' }]}
          >
            <Input placeholder="请输入策略代码 (英文)" />
          </Form.Item>
          <Form.Item
            name="strategy_type"
            label="类型"
            rules={[{ required: true, message: '请选择策略类型' }]}
          >
            <Select options={typeOptions} placeholder="请选择类型" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入策略描述" />
          </Form.Item>
          <Form.Item name="logic" label="策略逻辑">
            <Input.TextArea rows={3} placeholder="请输入策略逻辑说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Strategies;
