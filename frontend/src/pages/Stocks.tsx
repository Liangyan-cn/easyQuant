import { useState, useEffect, useCallback, useRef } from 'react';
import { Table, Input, Select, Space, Typography, message, Tabs } from 'antd';
import { SearchOutlined, UnorderedListOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import axios from 'axios';
import { stockApi } from '@/api/stock';
import type { StockInfo, StockListParams } from '@/types/stock';
import StockPoolTab from '@/components/StockPoolTab';

const { Title } = Typography;
const { Option } = Select;

const StockListTab: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stocks, setStocks] = useState<StockInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<StockListParams>({
    page: 1,
    size: 20,
    keyword: '',
    market: '',
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchStocks = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await stockApi.getStockList(params, {
        signal: abortControllerRef.current.signal,
      });
      setStocks(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      if (!axios.isCancel(error)) {
        message.error('获取股票列表失败');
      }
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchStocks();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchStocks]);

  const handleSearch = (value: string) => {
    setParams((prev) => ({ ...prev, keyword: value, page: 1 }));
  };

  const handleMarketChange = (value: string) => {
    setParams((prev) => ({ ...prev, market: value as StockListParams['market'], page: 1 }));
  };

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams((prev) => ({
      ...prev,
      page: pagination.current || 1,
      size: pagination.pageSize || 20,
    }));
  };

  const handleRowClick = (record: StockInfo) => {
    navigate(`/stocks/${record.code}`);
  };

  const columns: ColumnsType<StockInfo> = [
    {
      title: '代码',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '市场',
      dataIndex: 'market',
      key: 'market',
      width: 80,
      render: (market: string) => (market === 'SH' ? '沪市' : '深市'),
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 120,
    },
    {
      title: '最新价',
      dataIndex: 'latestPrice',
      key: 'latestPrice',
      width: 100,
      align: 'right',
      render: (price?: number) => (price != null ? price.toFixed(2) : '-'),
    },
    {
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      width: 100,
      align: 'right',
      render: (percent?: number) => {
        if (percent == null) return '-';
        const color = percent > 0 ? '#f5222d' : percent < 0 ? '#52c41a' : '#000';
        return <span style={{ color }}>{percent > 0 ? '+' : ''}{percent.toFixed(2)}%</span>;
      },
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      width: 120,
      align: 'right',
      render: (volume?: number) => {
        if (volume == null) return '-';
        if (volume >= 100000000) return `${(volume / 100000000).toFixed(2)}亿`;
        if (volume >= 10000) return `${(volume / 10000).toFixed(2)}万`;
        return volume.toString();
      },
    },
    {
      title: '成交额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (amount?: number) => {
        if (amount == null) return '-';
        if (amount >= 100000000) return `${(amount / 100000000).toFixed(2)}亿`;
        if (amount >= 10000) return `${(amount / 10000).toFixed(2)}万`;
        return amount.toFixed(2);
      },
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="搜索股票名称或代码"
          allowClear
          enterButton={<SearchOutlined />}
          style={{ width: 280 }}
          onSearch={handleSearch}
        />
        <Select
          value={params.market}
          onChange={handleMarketChange}
          style={{ width: 120 }}
          placeholder="选择市场"
        >
          <Option value="">全部市场</Option>
          <Option value="SH">沪市</Option>
          <Option value="SZ">深市</Option>
        </Select>
      </Space>
      <Table
        columns={columns}
        dataSource={stocks}
        rowKey="code"
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
        onRow={(record) => ({
          onClick: () => handleRowClick(record),
          style: { cursor: 'pointer' },
        })}
        scroll={{ x: 960 }}
      />
    </>
  );
};

const Stocks: React.FC = () => {
  const tabItems = [
    {
      key: 'pools',
      label: (
        <span>
          <AppstoreOutlined />
          股票池
        </span>
      ),
      children: <StockPoolTab />,
    },
    {
      key: 'list',
      label: (
        <span>
          <UnorderedListOutlined />
          股票列表
        </span>
      ),
      children: <StockListTab />,
    },
  ];

  return (
    <div>
      <Title level={3}>数据中心</Title>
      <Tabs defaultActiveKey="pools" items={tabItems} />
    </div>
  );
};

export default Stocks;
