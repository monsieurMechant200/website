from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re


# =========================
# USER MODELS
# =========================

class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: EmailStr
    is_admin: bool = False
    is_active: bool = True


class UserCreate(UserBase):
    """Create user model"""
    password: str


class UserInDB(UserBase):
    """User in database model"""
    id: str
    password_hash: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Update user model"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# =========================
# TIME SLOT MODELS
# =========================

class TimeSlotBase(BaseModel):
    """Base model for time slot"""
    date: date
    start_time: str
    end_time: str
    max_capacity: int = 5


class TimeSlotCreate(TimeSlotBase):
    """Create time slot model"""
    pass


class TimeSlotInDB(TimeSlotBase):
    """Time slot in database model"""
    id: str
    current_bookings: int = 0
    created_at: datetime
    updated_at: datetime


class TimeSlotUpdate(BaseModel):
    """Update time slot model"""
    max_capacity: Optional[int] = None
    current_bookings: Optional[int] = None


# =========================
# APPOINTMENT MODELS
# =========================

class AppointmentBase(BaseModel):
    """Base model for appointment"""
    order_id: Optional[str] = None
    time_slot_id: str
    client_email: EmailStr
    client_name: str
    client_phone: str
    service: str
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Create appointment model"""
    pass


class AppointmentInDB(AppointmentBase):
    """Appointment in database model"""
    id: str
    status: str = "confirmed"
    reminder_sent: bool = False
    created_at: datetime
    updated_at: datetime


class AppointmentUpdate(BaseModel):
    """Update appointment model"""
    status: Optional[str] = None
    time_slot_id: Optional[str] = None
    reminder_sent: Optional[bool] = None
    notes: Optional[str] = None


class AvailableSlotResponse(BaseModel):
    """Response model for available slots"""
    id: str
    date: date
    start_time: str
    end_time: str
    available_spots: int
    is_available: bool


# =========================
# ORDER MODELS
# =========================

class OrderBase(BaseModel):
    """Base order model"""
    service: str
    formula: str
    price: float
    client_name: str
    client_email: EmailStr
    client_phone: str
    client_description: Optional[str] = None
    
    @validator('client_phone')
    def validate_phone(cls, v):
        """Validate phone number"""
        phone = re.sub(r'[^\d+]', '', v)
        if len(phone) < 9:
            raise ValueError('Numéro de téléphone invalide')
        return phone


class OrderCreate(OrderBase):
    """Create order model with optional appointment"""
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    time_slot_id: Optional[str] = None


class OrderInDB(OrderBase):
    """Order in database model"""
    id: str
    status: str = "pending"
    appointment_id: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrderUpdate(BaseModel):
    """Update order model"""
    status: Optional[str] = None
    admin_notes: Optional[str] = None


# =========================
# MESSAGE MODELS
# =========================

class MessageBase(BaseModel):
    """Base message model"""
    name: str
    email: EmailStr
    subject: str
    message: str
    phone: Optional[str] = None


class MessageCreate(MessageBase):
    """Create message model"""
    pass


class MessageInDB(MessageBase):
    """Message in database model"""
    id: str
    status: str = "unread"
    read_at: Optional[datetime] = None
    created_at: datetime


class MessageUpdate(BaseModel):
    """Update message model"""
    status: Optional[str] = None
    read_at: Optional[datetime] = None


# =========================
# GALLERY MODELS
# =========================

class GalleryItemBase(BaseModel):
    """Base gallery item model"""
    title: str
    category: str
    description: Optional[str] = None
    image_url: str


class GalleryItemCreate(GalleryItemBase):
    """Create gallery item model"""
    pass


class GalleryItemInDB(GalleryItemBase):
    """Gallery item in database model"""
    id: str
    created_at: datetime


class GalleryItemUpdate(BaseModel):
    """Update gallery item model"""
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


# =========================
# SERVICE MODELS
# =========================

class ServiceBase(BaseModel):
    """Base service model"""
    name: str
    description: str
    category: str
    icon: str
    base_price: float = 0.0
    duration_minutes: int = 60
    active: bool = True


class ServiceCreate(ServiceBase):
    """Create service model"""
    formulas: Optional[List[dict]] = []


class ServiceInDB(ServiceBase):
    """Service in database model"""
    id: str
    formulas: List[dict] = []
    created_at: datetime
    updated_at: datetime


class ServiceUpdate(BaseModel):
    """Update service model"""
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    active: Optional[bool] = None


# =========================
# EMAIL MODELS
# =========================

class EmailTemplate(BaseModel):
    """Email template model"""
    template_type: str
    subject: str
    body: str
    variables: List[str] = []


# =========================
# STATS MODELS
# =========================

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_orders: int = 0
    pending_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0
    total_revenue: float = 0.0
    total_messages: int = 0
    unread_messages: int = 0
    total_appointments: int = 0
    upcoming_appointments: int = 0
    avg_order_value: float = 0.0
    conversion_rate: float = 0.0
