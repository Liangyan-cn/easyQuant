import pytest
from datetime import date, timedelta
from httpx import AsyncClient


@pytest.fixture
def test_account_data():
    return {
        "name": "Test Sandbox Account",
        "description": "Test account for unit testing",
        "initial_capital": 1000000.0,
    }


@pytest.fixture
def test_deployment_data():
    return {
        "strategy_id": 1,
        "name": "Test Deployment",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "allocation_ratio": 0.8,
    }


class TestSandboxAccountAPI:
    @pytest.mark.asyncio
    async def test_create_account(self, client: AsyncClient, test_account_data):
        response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_account_data["name"]
        assert data["initial_capital"] == test_account_data["initial_capital"]
        assert data["current_cash"] == test_account_data["initial_capital"]
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_accounts(self, client: AsyncClient):
        response = await client.get("/api/v1/sandbox/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    @pytest.mark.asyncio
    async def test_get_account_detail(self, client: AsyncClient, test_account_data):
        create_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/sandbox/accounts/{account_id}")
        assert response.status_code == 200
        data = response.json()
        assert "account" in data
        assert "positions" in data
        assert "recent_transactions" in data
        assert "deployments" in data
        assert "daily_values" in data

    @pytest.mark.asyncio
    async def test_update_account(self, client: AsyncClient, test_account_data):
        create_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = create_response.json()["id"]

        update_data = {"name": "Updated Account Name"}
        response = await client.put(
            f"/api/v1/sandbox/accounts/{account_id}",
            json=update_data,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Account Name"

    @pytest.mark.asyncio
    async def test_delete_account(self, client: AsyncClient, test_account_data):
        create_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/sandbox/accounts/{account_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_deposit(self, client: AsyncClient, test_account_data):
        create_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = create_response.json()["id"]
        initial_cash = create_response.json()["current_cash"]

        deposit_amount = 100000.0
        response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deposit",
            json={"amount": deposit_amount},
        )
        assert response.status_code == 200
        assert response.json()["current_cash"] == initial_cash + deposit_amount

    @pytest.mark.asyncio
    async def test_reset_account(self, client: AsyncClient, test_account_data):
        create_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = create_response.json()["id"]

        new_capital = 500000.0
        response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/reset",
            json={"initial_capital": new_capital},
        )
        assert response.status_code == 200
        assert response.json()["initial_capital"] == new_capital
        assert response.json()["current_cash"] == new_capital


class TestSandboxDeploymentAPI:
    @pytest.mark.asyncio
    async def test_create_deployment(self, client: AsyncClient, test_account_data, test_deployment_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json=test_deployment_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_deployment_data["name"]
        assert data["strategy_id"] == test_deployment_data["strategy_id"]
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_deployment(self, client: AsyncClient, test_account_data, test_deployment_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        deployment_response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json=test_deployment_data,
        )
        deployment_id = deployment_response.json()["id"]

        response = await client.get(f"/api/v1/sandbox/deployments/{deployment_id}")
        assert response.status_code == 200
        assert response.json()["id"] == deployment_id

    @pytest.mark.asyncio
    async def test_run_deployment(self, client: AsyncClient, test_account_data, test_deployment_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        deployment_response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json=test_deployment_data,
        )
        deployment_id = deployment_response.json()["id"]

        response = await client.post(f"/api/v1/sandbox/deployments/{deployment_id}/run")
        assert response.status_code == 200
        assert response.json()["status"] == "running"

    @pytest.mark.asyncio
    async def test_stop_deployment(self, client: AsyncClient, test_account_data, test_deployment_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        deployment_response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json=test_deployment_data,
        )
        deployment_id = deployment_response.json()["id"]

        await client.post(f"/api/v1/sandbox/deployments/{deployment_id}/run")

        response = await client.post(f"/api/v1/sandbox/deployments/{deployment_id}/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"


class TestSandboxCompareAPI:
    @pytest.mark.asyncio
    async def test_compare_strategies_empty(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sandbox/compare",
            json={"deployment_ids": [999, 998]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "start_date" in data
        assert "end_date" in data


class TestSandboxAccountValidation:
    @pytest.mark.asyncio
    async def test_create_account_invalid_capital(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sandbox/accounts",
            json={
                "name": "Invalid Account",
                "initial_capital": 100,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_account_empty_name(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sandbox/accounts",
            json={
                "name": "",
                "initial_capital": 1000000,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, client: AsyncClient):
        response = await client.get("/api/v1/sandbox/accounts/99999")
        assert response.status_code == 404


class TestSandboxDeploymentValidation:
    @pytest.mark.asyncio
    async def test_create_deployment_invalid_strategy(self, client: AsyncClient, test_account_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json={
                "strategy_id": 99999,
                "name": "Invalid Deployment",
                "start_date": str(date.today()),
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_deployment_invalid_dates(self, client: AsyncClient, test_account_data):
        account_response = await client.post(
            "/api/v1/sandbox/accounts",
            json=test_account_data,
        )
        account_id = account_response.json()["id"]

        response = await client.post(
            f"/api/v1/sandbox/accounts/{account_id}/deployments",
            json={
                "strategy_id": 1,
                "name": "Invalid Dates Deployment",
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today()),
            },
        )
        assert response.status_code == 400
