import pytest
from httpx import AsyncClient

from app.models.strategy import StrategyType, StrategyStatus


class TestStrategyAPI:
    @pytest.mark.asyncio
    async def test_get_strategies_list(self, client: AsyncClient):
        response = await client.get("/api/v1/strategies/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    @pytest.mark.asyncio
    async def test_get_strategies_with_pagination(self, client: AsyncClient):
        response = await client.get("/api/v1/strategies/", params={"page": 1, "size": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    @pytest.mark.asyncio
    async def test_get_strategies_by_type(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/strategies/",
            params={"strategy_type": "trend_following"}
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["strategy_type"] == "trend_following"

    @pytest.mark.asyncio
    async def test_get_strategy_by_id(self, client: AsyncClient):
        list_response = await client.get("/api/v1/strategies/")
        items = list_response.json()["items"]
        if items:
            strategy_id = items[0]["id"]
            response = await client.get(f"/api/v1/strategies/{strategy_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == strategy_id

    @pytest.mark.asyncio
    async def test_get_strategy_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/strategies/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_strategy(self, client: AsyncClient):
        strategy_data = {
            "name": "测试策略",
            "code": "test_strategy_001",
            "strategy_type": "custom",
            "description": "这是一个测试策略",
            "logic": "price > ma20 => BUY",
            "parameters": {"ma_period": 20}
        }
        response = await client.post("/api/v1/strategies/", json=strategy_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == strategy_data["name"]
        assert data["code"] == strategy_data["code"]
        assert data["strategy_type"] == strategy_data["strategy_type"]
        assert data["is_builtin"] == False

    @pytest.mark.asyncio
    async def test_create_strategy_duplicate_code(self, client: AsyncClient):
        strategy_data = {
            "name": "重复策略",
            "code": "ma_cross",
            "strategy_type": "custom",
        }
        response = await client.post("/api/v1/strategies/", json=strategy_data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_strategy(self, client: AsyncClient):
        create_data = {
            "name": "待更新策略",
            "code": "update_test_strategy",
            "strategy_type": "custom",
        }
        create_response = await client.post("/api/v1/strategies/", json=create_data)
        strategy_id = create_response.json()["id"]

        update_data = {
            "name": "已更新策略",
            "description": "更新后的描述",
        }
        response = await client.put(f"/api/v1/strategies/{strategy_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    @pytest.mark.asyncio
    async def test_delete_strategy(self, client: AsyncClient):
        create_data = {
            "name": "待删除策略",
            "code": "delete_test_strategy",
            "strategy_type": "custom",
        }
        create_response = await client.post("/api/v1/strategies/", json=create_data)
        strategy_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/strategies/{strategy_id}")
        assert response.status_code == 204

        get_response = await client.get(f"/api/v1/strategies/{strategy_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_builtin_strategy_forbidden(self, client: AsyncClient):
        list_response = await client.get("/api/v1/strategies/")
        items = list_response.json()["items"]
        builtin_strategies = [s for s in items if s["is_builtin"]]
        
        if builtin_strategies:
            strategy_id = builtin_strategies[0]["id"]
            response = await client.delete(f"/api/v1/strategies/{strategy_id}")
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_strategy_types(self, client: AsyncClient):
        response = await client.get("/api/v1/strategies/types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_builtin_strategies_initialized(self, client: AsyncClient):
        response = await client.get("/api/v1/strategies/")
        data = response.json()
        builtin_strategies = [s for s in data["items"] if s["is_builtin"]]
        assert len(builtin_strategies) >= 5

        builtin_codes = [s["code"] for s in builtin_strategies]
        expected_codes = ["ma_cross", "momentum", "mean_reversion", "bollinger_bands", "rsi_strategy"]
        for code in expected_codes:
            assert code in builtin_codes


class TestBacktestAPI:
    @pytest.mark.asyncio
    async def test_get_strategy_backtests(self, client: AsyncClient):
        list_response = await client.get("/api/v1/strategies/")
        items = list_response.json()["items"]
        if items:
            strategy_id = items[0]["id"]
            response = await client.get(f"/api/v1/strategies/{strategy_id}/backtests")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data

    @pytest.mark.asyncio
    async def test_create_backtest(self, client: AsyncClient):
        list_response = await client.get("/api/v1/strategies/")
        items = list_response.json()["items"]
        if items:
            strategy_id = items[0]["id"]
            backtest_data = {
                "strategy_id": strategy_id,
                "name": "测试回测",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 1000000,
                "commission_rate": 0.0003,
                "slippage": 0.001,
            }
            response = await client.post("/api/v1/strategies/backtests", json=backtest_data)
            assert response.status_code == 201
            data = response.json()
            assert data["strategy_id"] == strategy_id
            assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_backtest_invalid_strategy(self, client: AsyncClient):
        backtest_data = {
            "strategy_id": 99999,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }
        response = await client.post("/api/v1/strategies/backtests", json=backtest_data)
        assert response.status_code == 400
