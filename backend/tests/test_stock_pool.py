import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestStockPoolCRUD:
    async def test_create_stock_pool(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/stock-pools",
            json={"name": "测试池", "code": "test_pool", "description": "测试"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试池"
        assert data["code"] == "test_pool"
        assert data["pool_type"] == "user"

    async def test_get_stock_pools(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/stock-pools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_get_stock_pool_detail(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "详情测试", "code": "detail_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/stock-pools/{pool_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pool_id
        assert "items" in data

    async def test_update_stock_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "更新测试", "code": "update_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/stock-pools/{pool_id}",
            json={"name": "更新后名称"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后名称"

    async def test_delete_stock_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "删除测试", "code": "delete_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/stock-pools/{pool_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestStockPoolItems:
    async def test_add_stock_to_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "股票测试", "code": "stock_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/stock-pools/{pool_id}/stocks",
            json={"stock_code": "600519", "stock_name": "贵州茅台"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["stock_code"] == "600519"

    async def test_remove_stock_from_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "移除测试", "code": "remove_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/stock-pools/{pool_id}/stocks",
            json={"stock_code": "600519"},
            headers=auth_headers,
        )

        response = await client.delete(
            f"/api/v1/stock-pools/{pool_id}/stocks/600519",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestStockPoolPermissions:
    async def test_cannot_modify_system_pool(self, client: AsyncClient, auth_headers: dict):
        pools_resp = await client.get(
            "/api/v1/stock-pools?pool_type=system",
            headers=auth_headers,
        )
        if pools_resp.json()["total"] > 0:
            system_pool_id = pools_resp.json()["items"][0]["id"]
            response = await client.put(
                f"/api/v1/stock-pools/{system_pool_id}",
                json={"name": "尝试修改"},
                headers=auth_headers,
            )
            assert response.status_code == 403

    async def test_duplicate_code_rejected(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/v1/stock-pools",
            json={"name": "重复测试1", "code": "dup_code"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/stock-pools",
            json={"name": "重复测试2", "code": "dup_code"},
            headers=auth_headers,
        )
        assert response.status_code == 409
