"""FastAPI dependencies: JWT authentication and shared utilities."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config.settings import settings

_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


class TokenData(BaseModel):
    user_id: str


def verify_token(token: str) -> TokenData:
    """Decode and validate a JWT token. Raises HTTP 401 on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return TokenData(user_id=user_id)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenData:
    """FastAPI dependency that extracts and validates the Bearer JWT token.

    Returns TokenData with the authenticated user_id.
    Raises HTTP 401 if the token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    return verify_token(credentials.credentials)
