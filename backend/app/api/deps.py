from typing import Annotated, Optional, TypeVar

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.security import verify_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_db():
    async for session in _get_db():
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise UnauthorizedException(detail="Invalid token")
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user:
        raise UnauthorizedException(detail="User not found")
    if not user.is_active:
        raise UnauthorizedException(detail="User account is disabled")
    return user


async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(optional_security)],
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        return None
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        return None
    return user


T = TypeVar("T")


def get_resource_owner_id(resource: T) -> Optional[int]:
    if hasattr(resource, "user_id"):
        return resource.user_id
    if hasattr(resource, "created_by"):
        return resource.created_by
    return None


def verify_resource_ownership(resource: T, user: User, resource_name: str = "Resource") -> T:
    owner_id = get_resource_owner_id(resource)
    if owner_id is None:
        raise ForbiddenException(detail=f"Cannot verify ownership of {resource_name}")
    if owner_id != user.id:
        raise ForbiddenException(detail=f"You don't have permission to access this {resource_name}")
    return resource


async def get_owned_resource(
    resource: Optional[T],
    user: User,
    resource_name: str = "Resource",
) -> T:
    if not resource:
        raise NotFoundException(detail=f"{resource_name} not found")
    return verify_resource_ownership(resource, user, resource_name)
