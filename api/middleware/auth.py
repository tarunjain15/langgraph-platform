"""
Authentication Middleware - API key verification for hosted mode
"""

from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os


# HTTP Bearer token scheme
security = HTTPBearer()


def get_api_key_from_env() -> str:
    """Get API key from environment variable"""
    api_key = os.getenv("LGP_API_KEY")
    if not api_key:
        # For development, use a default key
        api_key = "dev-key-12345"
    return api_key


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """Verify API key from Authorization header

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    expected_key = get_api_key_from_env()

    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


# Optional: Rate limiting class (placeholder for R7)
class RateLimiter:
    """Rate limiter for API requests"""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        # TODO: Implement actual rate limiting logic

    async def check_rate_limit(self, client_id: str):
        """Check if client has exceeded rate limit"""
        # TODO: Implement rate limiting
        pass
