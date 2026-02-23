from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class HealthResponse(BaseModel):
    status: str
    message: str


class ResponseBase(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: Optional[DataT] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[Any] = None
