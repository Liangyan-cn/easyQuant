# easyQuant API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

大部分 API 需要 JWT Token 认证。在请求头中添加：

```
Authorization: Bearer <token>
```

---

## 认证 API

### POST /auth/register
注册新用户

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "username"
}
```

### POST /auth/login
用户登录

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## 股票数据 API

### GET /data/stocks/
获取股票列表

**Query Parameters:**
- `page` (int): 页码，默认 1
- `size` (int): 每页数量，默认 20
- `keyword` (string): 搜索关键词

### GET /data/stocks/{code}
获取股票详情

### GET /data/stocks/{code}/kline
获取 K 线数据

**Query Parameters:**
- `start_date` (string): 开始日期
- `end_date` (string): 结束日期
- `period` (string): 周期 (day/week/month)

---

## 因子 API

### GET /factors
获取因子列表

**Query Parameters:**
- `page` (int): 页码
- `size` (int): 每页数量
- `category` (string): 因子分类
- `keyword` (string): 搜索关键词

### GET /factors/{id}
获取因子详情

### POST /factors
创建因子

**Request Body:**
```json
{
  "name": "因子名称",
  "code": "factor_code",
  "category": "momentum",
  "formula": "close/open",
  "description": "因子描述"
}
```

### PUT /factors/{id}
更新因子

### DELETE /factors/{id}
删除因子

### POST /factors/calculate
计算因子值

**Request Body:**
```json
{
  "factor_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### POST /factors/evaluate
评估因子有效性

**Request Body:**
```json
{
  "factor_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

---

## 策略 API

### GET /strategies/
获取策略列表

**Query Parameters:**
- `page` (int): 页码
- `size` (int): 每页数量
- `strategy_type` (string): 策略类型
- `status` (string): 状态
- `keyword` (string): 搜索关键词

### GET /strategies/{id}
获取策略详情

### POST /strategies/
创建策略

**Request Body:**
```json
{
  "name": "策略名称",
  "code": "strategy_code",
  "strategy_type": "momentum",
  "description": "策略描述",
  "logic": "策略逻辑",
  "parameters": {"param1": 10}
}
```

### PUT /strategies/{id}
更新策略

### DELETE /strategies/{id}
删除策略

### GET /strategies/{id}/backtests
获取策略回测历史

### POST /strategies/backtests
创建回测任务

**Request Body:**
```json
{
  "strategy_id": 1,
  "name": "回测名称",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000,
  "commission_rate": 0.0003,
  "slippage": 0.001,
  "stock_pool": ["000001.SZ", "000002.SZ"]
}
```

### POST /strategies/backtests/{id}/run
执行回测

**Response:**
```json
{
  "status": "completed",
  "backtest_id": 1,
  "result": {
    "total_return": 0.15,
    "annual_return": 0.18,
    "max_drawdown": 0.08,
    "sharpe_ratio": 1.5,
    "total_trades": 50
  }
}
```

### GET /strategies/backtests/{id}
获取回测详情

### GET /strategies/backtests/{id}/orders
获取回测订单

### GET /strategies/backtests/{id}/positions
获取回测持仓

---

## 沙盒 API

### GET /sandbox/accounts
获取沙盒账户列表

**Query Parameters:**
- `page` (int): 页码，默认 1
- `size` (int): 每页数量，默认 20

### POST /sandbox/accounts
创建沙盒账户

**Request Body:**
```json
{
  "name": "我的沙盒账户",
  "description": "用于策略验证",
  "initial_capital": 1000000
}
```

### GET /sandbox/accounts/{id}
获取沙盒账户详情（包含持仓、交易记录、部署列表）

### PUT /sandbox/accounts/{id}
更新沙盒账户

### DELETE /sandbox/accounts/{id}
删除沙盒账户

### POST /sandbox/accounts/{id}/deposit
账户入金

**Request Body:**
```json
{
  "amount": 100000,
  "description": "追加资金"
}
```

### POST /sandbox/accounts/{id}/reset
重置账户（清空持仓和交易记录）

**Request Body:**
```json
{
  "initial_capital": 1000000
}
```

### POST /sandbox/accounts/{id}/deployments
创建策略部署

**Request Body:**
```json
{
  "strategy_id": 1,
  "name": "均线策略部署",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "allocation_ratio": 0.8,
  "stock_pool": ["000001.SZ", "000002.SZ"]
}
```

### GET /sandbox/deployments/{id}
获取部署详情

### POST /sandbox/deployments/{id}/run
执行策略部署

**Request Body:**
```json
{
  "run_date": "2024-06-15"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "running",
  "last_run_date": "2024-06-15",
  "last_run_result": {
    "signals": [...],
    "orders_executed": 3,
    "total_value": 1050000,
    "daily_return": 0.005
  }
}
```

### POST /sandbox/compare
多策略对比

**Request Body:**
```json
{
  "deployment_ids": [1, 2, 3],
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

**Response:**
```json
{
  "items": [
    {
      "deployment_id": 1,
      "strategy_name": "均线策略",
      "total_return": 0.15,
      "annual_return": 0.30,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.5,
      "volatility": 0.12,
      "win_rate": 0.55,
      "total_trades": 20,
      "daily_values": [...]
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

---

## 错误响应

所有 API 在出错时返回统一格式：

```json
{
  "detail": "错误描述"
}
```

**常见状态码:**
- 400: 请求参数错误
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 500: 服务器内部错误
