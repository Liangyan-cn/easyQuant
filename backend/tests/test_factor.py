import pytest
from httpx import AsyncClient


class TestFactorAPI:
    @pytest.mark.asyncio
    async def test_list_factors_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/factors")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["size"] == 20

    @pytest.mark.asyncio
    async def test_init_builtin_factors(self, client: AsyncClient):
        response = await client.post("/api/v1/factors/init-builtin")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] >= 0

    @pytest.mark.asyncio
    async def test_list_factors_after_init(self, client: AsyncClient):
        await client.post("/api/v1/factors/init-builtin")
        response = await client.get("/api/v1/factors")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_create_factor(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "测试因子",
            "code": "test_factor",
            "category": "custom",
            "description": "测试用因子",
            "formula": "close / open",
        }
        response = await client.post(
            "/api/v1/factors",
            json=factor_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试因子"
        assert data["code"] == "test_factor"
        assert data["category"] == "custom"
        assert data["is_builtin"] == False

    @pytest.mark.asyncio
    async def test_create_factor_duplicate_code(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "测试因子",
            "code": "duplicate_test",
            "category": "custom",
        }
        await client.post("/api/v1/factors", json=factor_data, headers=auth_headers)
        response = await client.post(
            "/api/v1/factors",
            json=factor_data,
            headers=auth_headers,
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_factor(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "获取测试因子",
            "code": "get_test_factor",
            "category": "momentum",
        }
        create_response = await client.post(
            "/api/v1/factors",
            json=factor_data,
            headers=auth_headers,
        )
        factor_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/factors/{factor_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == factor_id
        assert data["code"] == "get_test_factor"

    @pytest.mark.asyncio
    async def test_get_factor_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/factors/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_factor(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "更新测试因子",
            "code": "update_test_factor",
            "category": "value",
        }
        create_response = await client.post(
            "/api/v1/factors",
            json=factor_data,
            headers=auth_headers,
        )
        factor_id = create_response.json()["id"]

        update_data = {"name": "已更新的因子", "description": "更新后的描述"}
        response = await client.put(
            f"/api/v1/factors/{factor_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "已更新的因子"
        assert data["description"] == "更新后的描述"

    @pytest.mark.asyncio
    async def test_delete_factor(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "删除测试因子",
            "code": "delete_test_factor",
            "category": "quality",
        }
        create_response = await client.post(
            "/api/v1/factors",
            json=factor_data,
            headers=auth_headers,
        )
        factor_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/factors/{factor_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        get_response = await client.get(f"/api/v1/factors/{factor_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_factors_with_category_filter(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "分类测试因子",
            "code": "category_test_factor",
            "category": "growth",
        }
        await client.post("/api/v1/factors", json=factor_data, headers=auth_headers)

        response = await client.get("/api/v1/factors", params={"category": "growth"})
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "growth"

    @pytest.mark.asyncio
    async def test_list_factors_with_keyword_search(self, client: AsyncClient, auth_headers: dict):
        factor_data = {
            "name": "关键词测试因子",
            "code": "keyword_search_factor",
            "category": "technical",
        }
        await client.post("/api/v1/factors", json=factor_data, headers=auth_headers)

        response = await client.get("/api/v1/factors", params={"keyword": "关键词"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_category_stats(self, client: AsyncClient):
        response = await client.get("/api/v1/factors/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
