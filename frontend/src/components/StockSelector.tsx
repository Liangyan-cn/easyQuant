import { useState, useCallback, useRef } from 'react';
import { Select, Spin } from 'antd';
import type { SelectProps } from 'antd';
import debounce from 'lodash/debounce';
import { stockApi } from '@/api/stock';
import type { StockInfo } from '@/types/stock';

export interface StockOption {
  code: string;
  name: string;
  label: string;
  value: string;
}

interface StockSelectorProps extends Omit<SelectProps<string>, 'options' | 'onSearch'> {
  onStockSelect?: (stock: StockOption | null) => void;
}

const StockSelector: React.FC<StockSelectorProps> = ({
  onStockSelect,
  placeholder = '输入股票代码或名称搜索',
  ...props
}) => {
  const [options, setOptions] = useState<StockOption[]>([]);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchStocks = useCallback(
    debounce(async (keyword: string) => {
      if (!keyword || keyword.length < 1) {
        setOptions([]);
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setLoading(true);
      try {
        const response = await stockApi.getStockList(
          { keyword, page: 1, size: 20 },
          { signal: abortControllerRef.current.signal }
        );
        const newOptions = response.data.items.map((stock: StockInfo) => ({
          code: stock.code,
          name: stock.name,
          label: `${stock.code} - ${stock.name}`,
          value: stock.code,
        }));
        setOptions(newOptions);
      } catch {
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const handleSearch = (value: string) => {
    fetchStocks(value);
  };

  const handleChange = (value: string) => {
    const selected = options.find((opt) => opt.value === value);
    onStockSelect?.(selected || null);
  };

  const handleClear = () => {
    setOptions([]);
    onStockSelect?.(null);
  };

  return (
    <Select
      showSearch
      allowClear
      filterOption={false}
      onSearch={handleSearch}
      onChange={handleChange}
      onClear={handleClear}
      placeholder={placeholder}
      notFoundContent={loading ? <Spin size="small" /> : null}
      options={options}
      {...props}
    />
  );
};

export default StockSelector;
