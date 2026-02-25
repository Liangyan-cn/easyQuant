import os
from datetime import date, timedelta
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "false"

import hashlib

def _fast_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _fast_verify(plain_password: str, hashed_password: str) -> bool:
    return _fast_hash(plain_password) == hashed_password

import app.core.security as security_module
security_module.get_password_hash = _fast_hash
security_module.verify_password = _fast_verify

from app.core.database import get_db
from app.api.deps import get_db as deps_get_db
from app.main import app
from app.models import Base
from app.services.factor_service import init_builtin_factors
from app.services.strategy_service import init_builtin_strategies

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

test_async_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


_db_initialized = False


async def _init_database():
    global _db_initialized
    if not _db_initialized:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with test_async_session_maker() as session:
            await init_builtin_factors(session)
            await init_builtin_strategies(session)
        _db_initialized = True


async def _cleanup_user_data():
    from app.models.user import User
    from app.models.sandbox import (
        SandboxAccount, SandboxPosition, SandboxTransaction,
        SandboxDeployment, SandboxDailyValue
    )
    from app.models.factor import Factor
    from app.models.strategy import Strategy
    from app.models.stock_pool import StockPool, StockPoolItem
    async with test_async_session_maker() as session:
        await session.execute(SandboxDailyValue.__table__.delete())
        await session.execute(SandboxTransaction.__table__.delete())
        await session.execute(SandboxPosition.__table__.delete())
        await session.execute(SandboxDeployment.__table__.delete())
        await session.execute(SandboxAccount.__table__.delete())
        await session.execute(StockPoolItem.__table__.delete())
        await session.execute(StockPool.__table__.delete())
        await session.execute(Strategy.__table__.delete().where(Strategy.is_builtin == False))
        await session.execute(Factor.__table__.delete().where(Factor.is_builtin == False))
        await session.execute(User.__table__.delete())
        await session.commit()


def pytest_sessionfinish(session, exitstatus):
    import asyncio
    asyncio.get_event_loop().run_until_complete(test_engine.dispose())


_current_connection = None
_current_transaction = None


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    global _current_connection, _current_transaction
    if _current_connection is not None:
        async with test_async_session_maker(bind=_current_connection) as session:
            yield session
    else:
        async with test_async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    await _init_database()
    async with test_async_session_maker() as session:
        yield session
    await _cleanup_user_data()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps_get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    await _cleanup_user_data()
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "Test123456",
        "username": "testuser",
    }


@pytest.fixture
def test_user_data_2():
    return {
        "email": "test2@example.com",
        "password": "Test123456",
        "username": "testuser2",
    }


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user_data: dict) -> dict:
    await client.post("/api/v1/auth/register", json=test_user_data)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_mock_stock_list():
    from app.schemas.stock import StockInfo
    return [
        StockInfo(code="600519", name="贵州茅台", market="SH", industry="白酒"),
        StockInfo(code="000001", name="平安银行", market="SZ", industry="银行"),
        StockInfo(code="000002", name="万科A", market="SZ", industry="房地产"),
    ]


def _create_mock_ohlcv_items(code: str, start: date, end: date):
    from app.schemas.stock import OHLCVItem
    items = []
    current = start
    price = 100.0
    while current <= end:
        if current.weekday() < 5:
            items.append(OHLCVItem(
                date=current,
                open=price,
                high=price * 1.02,
                low=price * 0.98,
                close=price * 1.01,
                volume=1000000,
                amount=price * 1000000,
            ))
            price *= 1.001
        current += timedelta(days=1)
    return items


def _create_mock_history_response(code: str, period: str, start: date, end: date):
    from app.schemas.stock import StockHistoryResponse
    return StockHistoryResponse(
        code=code,
        period=period,
        items=_create_mock_ohlcv_items(code, start, end),
    )


@pytest.fixture(autouse=True)
def mock_akshare_apis():
    from app.schemas.stock import (
        StockListResponse, BalanceSheetResponse, IncomeStatementResponse,
        CashFlowResponse, FinancialIndicatorResponse, ValuationResponse, DividendResponse
    )
    
    mock_stocks = _create_mock_stock_list()
    
    def mock_get_stock_list(page=1, size=20, keyword=None, market=None, pool_code=None):
        filtered = mock_stocks
        if keyword:
            filtered = [s for s in filtered if keyword in s.code or keyword in s.name]
        if market:
            filtered = [s for s in filtered if s.market == market]
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        return StockListResponse(
            items=filtered[start_idx:end_idx],
            total=len(filtered),
            page=page,
            size=size,
        )
    
    def mock_get_stock_history(code, period="daily", start=None, end=None):
        if start is None:
            start = date.today() - timedelta(days=30)
        if end is None:
            end = date.today()
        return _create_mock_history_response(code, period, start, end)
    
    def mock_get_balance_sheet(code, limit=8):
        return BalanceSheetResponse(code=code, items=[])
    
    def mock_get_income_statement(code, limit=8):
        return IncomeStatementResponse(code=code, items=[])
    
    def mock_get_cash_flow(code, limit=8):
        return CashFlowResponse(code=code, items=[])
    
    def mock_get_financial_indicators(code, limit=8):
        return FinancialIndicatorResponse(code=code, items=[])
    
    def mock_get_valuation(code, limit=30):
        return ValuationResponse(code=code, items=[])
    
    def mock_get_dividend(code):
        return DividendResponse(code=code, items=[])
    
    with patch("app.api.v1.endpoints.data.get_stock_list", side_effect=mock_get_stock_list), \
         patch("app.api.v1.endpoints.data.get_stock_history", side_effect=mock_get_stock_history), \
         patch("app.api.v1.endpoints.data.get_balance_sheet", side_effect=mock_get_balance_sheet), \
         patch("app.api.v1.endpoints.data.get_income_statement", side_effect=mock_get_income_statement), \
         patch("app.api.v1.endpoints.data.get_cash_flow", side_effect=mock_get_cash_flow), \
         patch("app.api.v1.endpoints.data.get_financial_indicators", side_effect=mock_get_financial_indicators), \
         patch("app.api.v1.endpoints.data.get_valuation", side_effect=mock_get_valuation), \
         patch("app.api.v1.endpoints.data.get_dividend", side_effect=mock_get_dividend), \
         patch("app.services.sandbox_engine.get_stock_history", side_effect=mock_get_stock_history), \
         patch("app.services.sandbox_engine.get_stock_list", side_effect=mock_get_stock_list):
        yield
