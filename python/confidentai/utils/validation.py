from typing import Optional, TypeVar

T = TypeVar("T")


def require(value: Optional[T], message: str) -> T:
    if not value:
        raise ValueError(message)
    return value
