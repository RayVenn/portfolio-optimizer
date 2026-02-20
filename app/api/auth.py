import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    expected_key = os.environ.get("API_KEY")
    if expected_key is None:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
