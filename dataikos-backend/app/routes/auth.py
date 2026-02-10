from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas import LoginRequest, TokenResponse, RefreshTokenRequest
from app.auth import auth_handler
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Login user and return JWT tokens"""
    user = await auth_handler.authenticate_user(
        credentials.username,
        credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = auth_handler.create_tokens(user)
    
    logger.info(f"User logged in: {user['username']}")
    
    return tokens


@router.post("/logout")
async def logout(current_user: dict = Depends(auth_handler.get_current_user)):
    """Logout user (client-side token deletion)"""
    logger.info(f"User logged out: {current_user['username']}")
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    new_token = await auth_handler.refresh_access_token(request.refresh_token)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return new_token


@router.get("/validate-token")
async def validate_token(current_user: dict = Depends(auth_handler.get_current_user)):
    """Validate current access token"""
    return {
        "valid": True,
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user.get("email"),
            "is_admin": current_user.get("is_admin", False)
        }
    }


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(auth_handler.get_current_user)):
    """Get current user information"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email"),
        "is_admin": current_user.get("is_admin", False),
        "is_active": current_user.get("is_active", True),
        "created_at": current_user.get("created_at")
    }
