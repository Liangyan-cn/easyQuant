import { useState, useEffect, useCallback, useRef } from 'react';
import { Table, Input, Select, Space, Typography, Button, Tag, Modal, Form, message, Popconfirm, Tooltip, Alert } from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined, ExperimentOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import axios from 'axios';
import { factorApi } from '@/api/factor';
import type { Factor, FactorCategory, FactorListParams, FactorCreate } from '@/types/factor';
import { FACTOR_CATEGORY_LABELS } from '@/types/factor';

const { Title } = Typography;

const categoryOptions = Object.entries(FACTOR_CATEGORY_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const Factors: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [factors, setFactors] = useState<Factor[]>([]);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<FactorListParams>({
    page: 1,
    size: 20,
    keyword: '',
    category: undefined,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFactor, setEditingFactor] = useState<Factor | null>(null);
  const [form] = Form.useForm();
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchFactors = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await factorApi.getFactorList(params, {
        signal: abortControllerRef.current.signal,
      });
      setFactors(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      if (!axios.isCancel(error)) {
        message.error('获取因子列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchFactors();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchFactors]);

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

  const handleCategoryChange = (value: FactorCategory | undefined) => {
    setParams((prev) => ({ ...prev, category: value, page: 1 }));
  };

  const handleCreate = () => {
    setEditingFactor(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (factor: Factor) => {
    setEditingFactor(factor);
    form.setFieldsValue(factor);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await factorApi.deleteFactor(id);
      message.success('删除成功');
      fetchFactors();
    } catch {
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingFactor) {
        await factorApi.updateFactor(editingFactor.id, values);
        message.success('更新成功');
      } else {
        await factorApi.createFactor(values as FactorCreate);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchFactors();
    } catch {
      message.error('操作失败');
    }
  };

  const handleInitBuiltin = async () => {
    try {
      const response = await factorApi.initBuiltinFactors();
      const count = response.data.message.match(/\d+/)?.[0] || '0';
      if (count === '0') {
        message.info('内置因子已存在，无需重复初始化');
      } else {
        message.success(`成功初始化 ${count} 个内置因子`);
      }
      fetchFactors();
    } catch {
      message.error('初始化失败');
    }
  };

  const columns: ColumnsType<Factor> = [
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
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: FactorCategory) => (
        <Tag color="blue">{FACTOR_CATEGORY_LABELS[category]}</Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'is_builtin',
      key: 'is_builtin',
      width: 80,
      render: (isBuiltin: boolean) => (
        <Tag color={isBuiltin ? 'green' : 'orange'}>{isBuiltin ? '内置' : '自定义'}</Tag>
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
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => navigate(`/factors/${record.id}`)}
          >
            详情
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
                title="确定删除此因子？"
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
        <Title level={4} style={{ margin: 0 }}>因子管理</Title>
        <Space>
          <Tooltip title="首次使用时点击，将创建系统预置的常用因子（如PE、ROE、动量等）">
            <Button onClick={handleInitBuiltin}>
              初始化内置因子
              <QuestionCircleOutlined style={{ marginLeft: 4, color: '#999' }} />
            </Button>
          </Tooltip>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建因子
          </Button>
        </Space>
      </div>

      {factors.length === 0 && !loading && (
        <Alert
          message="开始使用因子"
          description="点击「初始化内置因子」按钮创建系统预置因子，或点击「新建因子」创建自定义因子。因子用于量化选股，如市盈率(PE)、净资产收益率(ROE)等。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索因子名称或代码"
          allowClear
          onSearch={handleSearch}
          style={{ width: 250 }}
          prefix={<SearchOutlined />}
        />
        <Select
          placeholder="选择分类"
          allowClear
          style={{ width: 150 }}
          options={categoryOptions}
          onChange={handleCategoryChange}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={factors}
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
        title={editingFactor ? '编辑因子' : '新建因子'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入因子名称' }]}
          >
            <Input placeholder="请输入因子名称" />
          </Form.Item>
          <Form.Item
            name="code"
            label="代码"
            rules={[{ required: true, message: '请输入因子代码' }]}
          >
            <Input placeholder="请输入因子代码 (英文)" />
          </Form.Item>
          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择因子分类' }]}
          >
            <Select options={categoryOptions} placeholder="请选择分类" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入因子描述" />
          </Form.Item>
          <Form.Item name="formula" label="公式">
            <Input.TextArea rows={3} placeholder="请输入因子公式 (Python 表达式)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Factors;
