import pytest
from httpx import AsyncClient


class TestStockList:
    async def test_get_stocks_list(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)

    async def test_get_stocks_with_pagination(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["items"]) <= 5

    async def test_get_stocks_with_keyword(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks?keyword=600519")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        if data["total"] > 0:
            assert any("600519" in item["code"] for item in data["items"])

    async def test_get_stocks_with_market_filter(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks?market=SH")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert item["market"] == "SH"


class TestStockHistory:
    async def test_get_stock_history_daily(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/data/stocks/600519/history?period=daily&start=2024-01-01&end=2024-01-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert data["period"] == "daily"
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_get_stock_history_weekly(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/data/stocks/600519/history?period=weekly&start=2024-01-01&end=2024-03-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "weekly"

    async def test_get_stock_history_with_date_range(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/data/stocks/600519/history?period=daily&start=2024-01-01&end=2024-01-10"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert "date" in item
            assert "open" in item
            assert "high" in item
            assert "low" in item
            assert "close" in item
            assert "volume" in item

    async def test_get_stock_history_default_period(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/data/stocks/600519/history"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "daily"
