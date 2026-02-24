import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Drawer,
  List,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  RightOutlined,
} from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { stockPoolApi } from '@/api/stockPool';
import type {
  StockPool,
  StockPoolDetail,
  StockPoolListParams,
  StockPoolCreate,
  StockPoolUpdate,
  StockPoolItemCreate,
  StockPoolItem,
} from '@/types/stockPool';
import { POOL_TYPE_LABELS } from '@/types/stockPool';

const StockPoolTab: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [pools, setPools] = useState<StockPool[]>([]);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<StockPoolListParams>({
    page: 1,
    size: 20,
  });

  const [modalVisible, setModalVisible] = useState(false);
  const [editingPool, setEditingPool] = useState<StockPool | null>(null);
  const [form] = Form.useForm();

  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedPool, setSelectedPool] = useState<StockPoolDetail | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [addStockForm] = Form.useForm();
  const [stockSearchKeyword, setStockSearchKeyword] = useState('');

  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchPools = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await stockPoolApi.getPoolList(params, {
        signal: abortControllerRef.current.signal,
      });
      setPools(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      if (!axios.isCancel(error)) {
        message.error('获取股票池列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchPools();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchPools]);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams((prev) => ({
      ...prev,
      page: pagination.current || 1,
      size: pagination.pageSize || 20,
    }));
  };

  const handleCreate = () => {
    setEditingPool(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (pool: StockPool) => {
    setEditingPool(pool);
    form.setFieldsValue(pool);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await stockPoolApi.deletePool(id);
      message.success('删除成功');
      fetchPools();
    } catch {
      message.error('删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingPool) {
        const updateData: StockPoolUpdate = {
          name: values.name,
          description: values.description,
        };
        await stockPoolApi.updatePool(editingPool.id, updateData);
        message.success('更新成功');
      } else {
        const createData: StockPoolCreate = values;
        await stockPoolApi.createPool(createData);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchPools();
    } catch {
      message.error(editingPool ? '更新失败' : '创建失败');
    }
  };

  const handleViewDetail = async (pool: StockPool) => {
    setDrawerVisible(true);
    setDrawerLoading(true);
    setStockSearchKeyword('');
    try {
      const response = await stockPoolApi.getPool(pool.id);
      setSelectedPool(response.data);
    } catch {
      message.error('获取股票池详情失败');
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleAddStock = async () => {
    if (!selectedPool) return;
    try {
      const values = await addStockForm.validateFields();
      const data: StockPoolItemCreate = {
        stock_code: values.stock_code,
        stock_name: values.stock_name,
      };
      await stockPoolApi.addStock(selectedPool.id, data);
      message.success('添加成功');
      addStockForm.resetFields();
      const response = await stockPoolApi.getPool(selectedPool.id);
      setSelectedPool(response.data);
      fetchPools();
    } catch {
      message.error('添加失败');
    }
  };

  const handleRemoveStock = async (stockCode: string) => {
    if (!selectedPool) return;
    try {
      await stockPoolApi.removeStock(selectedPool.id, stockCode);
      message.success('删除成功');
      const response = await stockPoolApi.getPool(selectedPool.id);
      setSelectedPool(response.data);
      fetchPools();
    } catch {
      message.error('删除失败');
    }
  };

  const handleStockClick = (stockCode: string) => {
    navigate(`/stocks/${stockCode}`);
  };

  const filteredStocks = selectedPool?.items.filter((item: StockPoolItem) => {
    if (!stockSearchKeyword) return true;
    const keyword = stockSearchKeyword.toLowerCase();
    return (
      item.stock_code.toLowerCase().includes(keyword) ||
      (item.stock_name && item.stock_name.toLowerCase().includes(keyword))
    );
  }) || [];

  const columns: ColumnsType<StockPool> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '代码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '类型',
      dataIndex: 'pool_type',
      key: 'pool_type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'system' ? 'blue' : 'green'}>
          {POOL_TYPE_LABELS[type as keyof typeof POOL_TYPE_LABELS]}
        </Tag>
      ),
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 100,
      align: 'right',
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
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          {record.pool_type === 'user' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Popconfirm
                title="确定删除此股票池？"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建股票池
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={pools}
        rowKey="id"
        loading={loading}
        pagination={{
          current: params.page,
          pageSize: params.size,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        onChange={handleTableChange}
      />

      <Modal
        title={editingPool ? '编辑股票池' : '新建股票池'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入股票池名称" />
          </Form.Item>
          {!editingPool && (
            <Form.Item
              name="code"
              label="代码"
              rules={[
                { required: true, message: '请输入代码' },
                { pattern: /^[a-z0-9_]+$/, message: '只能包含小写字母、数字和下划线' },
              ]}
            >
              <Input placeholder="请输入股票池代码，如 my_watchlist" />
            </Form.Item>
          )}
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={selectedPool?.name || '股票池详情'}
        placement="right"
        width={500}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {drawerLoading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>加载中...</div>
        ) : selectedPool ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <Tag color={selectedPool.pool_type === 'system' ? 'blue' : 'green'}>
                {POOL_TYPE_LABELS[selectedPool.pool_type]}
              </Tag>
              <span style={{ marginLeft: 8, color: '#666' }}>
                {selectedPool.description}
              </span>
            </div>

            {selectedPool.pool_type === 'user' && (
              <Form
                form={addStockForm}
                layout="inline"
                style={{ marginBottom: 16 }}
                onFinish={handleAddStock}
              >
                <Form.Item
                  name="stock_code"
                  rules={[{ required: true, message: '请输入股票代码' }]}
                >
                  <Input placeholder="股票代码" style={{ width: 120 }} />
                </Form.Item>
                <Form.Item name="stock_name">
                  <Input placeholder="股票名称(可选)" style={{ width: 120 }} />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                    添加
                  </Button>
                </Form.Item>
              </Form>
            )}

            <Input.Search
              placeholder="搜索股票代码或名称"
              allowClear
              value={stockSearchKeyword}
              onChange={(e) => setStockSearchKeyword(e.target.value)}
              style={{ marginBottom: 16 }}
            />

            {filteredStocks.length > 0 ? (
              <List
                size="small"
                bordered
                dataSource={filteredStocks}
                renderItem={(item: StockPoolItem) => (
                  <List.Item
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleStockClick(item.stock_code)}
                    actions={
                      selectedPool.pool_type === 'user'
                        ? [
                            <Popconfirm
                              key="delete"
                              title="确定删除此股票？"
                              onConfirm={(e) => {
                                e?.stopPropagation();
                                handleRemoveStock(item.stock_code);
                              }}
                              onCancel={(e) => e?.stopPropagation()}
                            >
                              <Button
                                type="link"
                                size="small"
                                danger
                                onClick={(e) => e.stopPropagation()}
                              >
                                删除
                              </Button>
                            </Popconfirm>,
                            <RightOutlined
                              key="go"
                              style={{ color: '#999' }}
                              onClick={() => handleStockClick(item.stock_code)}
                            />,
                          ]
                        : [
                            <RightOutlined
                              key="go"
                              style={{ color: '#999' }}
                              onClick={() => handleStockClick(item.stock_code)}
                            />,
                          ]
                    }
                  >
                    <span style={{ fontWeight: 500, color: '#1890ff' }}>
                      {item.stock_code}
                    </span>
                    <span style={{ marginLeft: 8, color: '#666' }}>
                      {item.stock_name || '-'}
                    </span>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description={stockSearchKeyword ? '未找到匹配的股票' : '暂无股票'} />
            )}
          </>
        ) : null}
      </Drawer>
    </div>
  );
};

export default StockPoolTab;
