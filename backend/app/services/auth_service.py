from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import Token, UserCreate


REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, user_data: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ConflictException(detail="Email already registered")
        return await self.user_repo.create(user_data)

    async def login(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException(detail="Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedException(detail="User account is disabled")
        return self._create_tokens(user.id)

    async def refresh_token(self, refresh_token: str) -> Token:
        user_id = verify_token(refresh_token)
        if not user_id:
            raise UnauthorizedException(detail="Invalid refresh token")
        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException(detail="User not found or inactive")
        return self._create_tokens(user.id)

    async def get_current_user(self, token: str) -> User:
        user_id = verify_token(token)
        if not user_id:
            raise UnauthorizedException(detail="Invalid token")
        user = await self.user_repo.get_by_id(int(user_id))
        if not user:
            raise UnauthorizedException(detail="User not found")
        if not user.is_active:
            raise UnauthorizedException(detail="User account is disabled")
        return user

    def _create_tokens(self, user_id: int) -> Token:
        access_token = create_access_token(subject=user_id)
        refresh_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
