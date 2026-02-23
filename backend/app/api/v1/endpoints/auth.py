from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.register(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login(user_data.email, user_data.password)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_token(credentials.credentials)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(credentials.credentials)
