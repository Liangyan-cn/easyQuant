import { useState, useEffect, useCallback, useRef } from 'react';
import { Table, Input, Space, Typography, Button, Tag, Modal, Form, message, Popconfirm, InputNumber } from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import axios from 'axios';
import { sandboxApi } from '@/api/sandbox';
import type { SandboxAccount, SandboxStatus, SandboxAccountListParams, SandboxAccountCreate } from '@/types/sandbox';
import { SANDBOX_STATUS_LABELS } from '@/types/sandbox';

const { Title } = Typography;

const Sandbox: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState<SandboxAccount[]>([]);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<SandboxAccountListParams>({
    page: 1,
    size: 20,
  });
  const [keyword, setKeyword] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<SandboxAccount | null>(null);
  const [form] = Form.useForm();
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchAccounts = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await sandboxApi.getAccountList(params, {
        signal: abortControllerRef.current.signal,
      });
      let items = response.data.items;
      if (keyword) {
        items = items.filter(
          (item) =>
            item.name.toLowerCase().includes(keyword.toLowerCase()) ||
            item.description?.toLowerCase().includes(keyword.toLowerCase())
        );
      }
      setAccounts(items);
      setTotal(response.data.total);
    } catch (error) {
      if (!axios.isCancel(error)) {
        message.error('获取沙盒账户列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, [params, keyword]);

  useEffect(() => {
    fetchAccounts();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchAccounts]);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams((prev) => ({
      ...prev,
      page: pagination.current || 1,
      size: pagination.pageSize || 20,
    }));
  };

  const handleSearch = (value: string) => {
    setKeyword(value);
    setParams((prev) => ({ ...prev, page: 1 }));
  };

  const handleCreate = () => {
    setEditingAccount(null);
    form.resetFields();
    form.setFieldsValue({ initial_capital: 1000000 });
    setModalVisible(true);
  };

  const handleEdit = (account: SandboxAccount) => {
    setEditingAccount(account);
    form.setFieldsValue({
      name: account.name,
      description: account.description,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await sandboxApi.deleteAccount(id);
      message.success('删除成功');
      fetchAccounts();
    } catch {
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingAccount) {
        await sandboxApi.updateAccount(editingAccount.id, {
          name: values.name,
          description: values.description,
        });
        message.success('更新成功');
      } else {
        await sandboxApi.createAccount(values as SandboxAccountCreate);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchAccounts();
    } catch {
      message.error('操作失败');
    }
  };

  const getStatusColor = (status: SandboxStatus) => {
    const colors: Record<SandboxStatus, string> = {
      active: 'green',
      paused: 'orange',
      stopped: 'default',
    };
    return colors[status];
  };

  const formatCurrency = (value: number) => {
    return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatReturn = (initial: number, current: number) => {
    const returnRate = ((current - initial) / initial) * 100;
    const color = returnRate >= 0 ? '#3f8600' : '#cf1322';
    return <span style={{ color }}>{returnRate >= 0 ? '+' : ''}{returnRate.toFixed(2)}%</span>;
  };

  const columns: ColumnsType<SandboxAccount> = [
    {
      title: '账户名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '初始资金',
      dataIndex: 'initial_capital',
      key: 'initial_capital',
      width: 150,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '当前现金',
      dataIndex: 'current_cash',
      key: 'current_cash',
      width: 150,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '总资产',
      dataIndex: 'total_value',
      key: 'total_value',
      width: 150,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '收益率',
      key: 'return',
      width: 100,
      render: (_, record) => formatReturn(record.initial_capital, record.total_value),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: SandboxStatus) => (
        <Tag color={getStatusColor(status)}>{SANDBOX_STATUS_LABELS[status]}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (value: string) => value.split('T')[0],
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/sandbox/${record.id}`)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此沙盒账户？"
            description="删除后所有相关数据将被清除"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>沙盒账户</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建账户
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索账户名称或描述"
          allowClear
          onSearch={handleSearch}
          style={{ width: 300 }}
          prefix={<SearchOutlined />}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={accounts}
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
        title={editingAccount ? '编辑账户' : '新建沙盒账户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="账户名称"
            rules={[{ required: true, message: '请输入账户名称' }]}
          >
            <Input placeholder="请输入账户名称" maxLength={100} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入账户描述" />
          </Form.Item>
          {!editingAccount && (
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
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default Sandbox;
