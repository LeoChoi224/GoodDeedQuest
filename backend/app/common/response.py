from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success") -> "APIResponse":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str = "Failure", data: Any = None) -> "APIResponse":
        return cls(success=False, message=message, data=data)
