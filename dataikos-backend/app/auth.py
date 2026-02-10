from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.utils.supabase_client import db_manager
from app.config import settings
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthHandler:
    """Handle authentication and authorization"""
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        try:
            user = db_manager.get_user_by_username(username)
            
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            if not verify_password(password, user.get('password_hash', '')):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            if not user.get('is_active', True):
                logger.warning(f"Inactive user attempted login: {username}")
                return None
            
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": user_data['username'],
            "user_id": user_data['id'],
            "email": user_data.get('email'),
            "is_admin": user_data.get('is_admin', False)
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Get current user from token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            token = credentials.credentials
            payload = verify_token(token)
            
            if payload is None:
                raise credentials_exception
            
            username: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if username is None or token_type != "access":
                raise credentials_exception
            
            user = db_manager.get_user_by_username(username)
            if user is None:
                raise credentials_exception
            
            return user
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise credentials_exception
    
    @staticmethod
    async def get_current_admin(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Verify current user is admin"""
        if not current_user.get('is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        try:
            payload = verify_token(refresh_token)
            
            if payload is None or payload.get("type") != "refresh":
                return None
            
            username: str = payload.get("sub")
            if username is None:
                return None
            
            user = db_manager.get_user_by_username(username)
            if user is None:
                return None
            
            # Create new access token
            token_data = {
                "sub": user['username'],
                "user_id": user['id'],
                "email": user.get('email'),
                "is_admin": user.get('is_admin', False)
            }
            
            new_access_token = create_access_token(token_data)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            return None


# Global instance
auth_handler = AuthHandler()


# Fix the circular dependency for get_current_admin
AuthHandler.get_current_admin = staticmethod(
    lambda current_user=Depends(AuthHandler.get_current_user): 
    auth_handler._verify_admin(current_user)
)


def _verify_admin(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """Internal method to verify admin status"""
    if not current_user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


AuthHandler._verify_admin = _verify_admin
