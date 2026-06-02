from typing import Dict, Mapping, Optional


def drop_none(data: Optional[Mapping]) -> Optional[Dict]:
    if data is None:
        return None
    return {key: value for key, value in data.items() if value is not None}


def join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
