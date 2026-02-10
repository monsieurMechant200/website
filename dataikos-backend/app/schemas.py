from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import re


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class OrderFilter(BaseModel):
    """Order filter schema"""
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    service: Optional[str] = None
    client_email: Optional[str] = None


class MessageFilter(BaseModel):
    """Message filter schema"""
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    email: Optional[str] = None


class GalleryFilter(BaseModel):
    """Gallery filter schema"""
    category: Optional[str] = None
    search: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    """Bulk delete request schema"""
    ids: List[str]
    
    @validator('ids')
    def validate_ids(cls, v):
        if not v:
            raise ValueError('IDs list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot delete more than 100 items at once')
        return v


class EmailRequest(BaseModel):
    """Email request schema"""
    to_email: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters schema"""
    page: int = 1
    limit: int = 20
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be >= 1')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v


class PhoneValidator(BaseModel):
    """Phone number validator"""
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        # Cameroon phone numbers + international
        phone_pattern = r'^(\+?237)?[6-9][0-9]{8}$|^\+?[0-9]{10,15}$'
        clean_phone = v.replace(' ', '').replace('-', '')
        if not re.match(phone_pattern, clean_phone):
            raise ValueError('Invalid phone number format')
        return clean_phone


class DateRangeFilter(BaseModel):
    """Date range filter schema"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v:
            from datetime import datetime
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Date must be in ISO format (YYYY-MM-DD)')
        return v
