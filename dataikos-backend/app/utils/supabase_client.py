import logging
from typing import Dict, Any, List, Optional
from datetime import date, time, datetime, timedelta

from supabase import create_client, Client
from app.config import settings
from app.utils.security import get_password_hash

logger = logging.getLogger(__name__)


# =========================
# Supabase Client Singleton
# =========================

class SupabaseClient:
    """Singleton for Supabase client instances"""
    _instance: Optional[Client] = None
    _service_instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get regular Supabase client"""
        if cls._instance is None:
            try:
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error("Supabase init failed", exc_info=True)
                raise
        return cls._instance

    @classmethod
    def get_service_client(cls) -> Client:
        """Get service role Supabase client"""
        if cls._service_instance is None:
            try:
                cls._service_instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                logger.info("Supabase service client initialized")
            except Exception as e:
                logger.error("Supabase service init failed", exc_info=True)
                raise
        return cls._service_instance


# =================
# Database Manager
# =================

class DatabaseManager:
    """Centralized database operations manager"""

    def __init__(self):
        self.client = SupabaseClient.get_client()
        self.service_client = SupabaseClient.get_service_client()

    # ==================
    # INITIALIZATION
    # ==================

    def initialize_database(self):
        """Initialize database with default admin user"""
        try:
            logger.info("Initializing database...")
            
            # Check if admin user exists
            if settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD:
                existing_admin = self.get_user_by_username(settings.ADMIN_USERNAME)
                
                if not existing_admin:
                    # Create admin user
                    admin_data = {
                        "username": settings.ADMIN_USERNAME,
                        "email": settings.ADMIN_EMAIL or f"{settings.ADMIN_USERNAME}@dataikos.com",
                        "password_hash": get_password_hash(settings.ADMIN_PASSWORD),
                        "is_admin": True,
                        "is_active": True,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    self.create_user(admin_data)
                    logger.info(f"Admin user created: {settings.ADMIN_USERNAME}")
                else:
                    logger.info("Admin user already exists")
            
            logger.info("Database initialization complete")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)

    # ==================
    # USERS
    # ==================

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            res = (
                self.client.table("users")
                .select("*")
                .eq("username", username)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_user_by_username failed: {e}", exc_info=True)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            res = (
                self.client.table("users")
                .select("*")
                .eq("email", email)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_user_by_email failed: {e}", exc_info=True)
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            res = self.client.table("users").insert(user_data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_user failed: {e}", exc_info=True)
            return None

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user"""
        try:
            res = (
                self.client.table("users")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"update_user failed: {e}", exc_info=True)
            return None

    # ==================
    # ORDERS
    # ==================

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new order"""
        try:
            res = self.client.table("orders").insert(order_data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_order failed: {e}", exc_info=True)
            return None

    def get_orders(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders with optional filters"""
        try:
            query = self.client.table("orders").select("*")

            if filters:
                for k, v in filters.items():
                    if v is not None:
                        query = query.eq(k, v)

            res = (
                query.order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"get_orders failed: {e}", exc_info=True)
            return []

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            res = (
                self.client.table("orders")
                .select("*")
                .eq("id", order_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_order_by_id failed: {e}", exc_info=True)
            return None

    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update order"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            res = (
                self.client.table("orders")
                .update(update_data)
                .eq("id", order_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"update_order failed: {e}", exc_info=True)
            return None

    def delete_order(self, order_id: str) -> bool:
        """Delete order"""
        try:
            res = (
                self.client.table("orders")
                .delete()
                .eq("id", order_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"delete_order failed: {e}", exc_info=True)
            return False

    # ==================
    # MESSAGES
    # ==================

    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new message"""
        try:
            res = self.client.table("contact_messages").insert(message_data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_message failed: {e}", exc_info=True)
            return None

    def get_messages(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages with optional filters"""
        try:
            query = self.client.table("contact_messages").select("*")

            if filters:
                for k, v in filters.items():
                    if v is not None:
                        query = query.eq(k, v)

            res = (
                query.order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"get_messages failed: {e}", exc_info=True)
            return []

    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message by ID"""
        try:
            res = (
                self.client.table("contact_messages")
                .select("*")
                .eq("id", message_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_message_by_id failed: {e}", exc_info=True)
            return None

    def update_message(self, message_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update message"""
        try:
            res = (
                self.client.table("contact_messages")
                .update(update_data)
                .eq("id", message_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"update_message failed: {e}", exc_info=True)
            return None

    def delete_message(self, message_id: str) -> bool:
        """Delete message"""
        try:
            res = (
                self.client.table("contact_messages")
                .delete()
                .eq("id", message_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"delete_message failed: {e}", exc_info=True)
            return False

    # ==================
    # GALLERY
    # ==================

    def create_gallery_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new gallery item"""
        try:
            res = self.client.table("gallery").insert(item_data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_gallery_item failed: {e}", exc_info=True)
            return None

    def get_gallery_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get gallery items with optional filters"""
        try:
            query = self.client.table("gallery").select("*")

            if filters:
                for k, v in filters.items():
                    if v is not None:
                        query = query.eq(k, v)

            res = (
                query.order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"get_gallery_items failed: {e}", exc_info=True)
            return []

    def delete_gallery_item(self, item_id: str) -> bool:
        """Delete gallery item"""
        try:
            res = (
                self.client.table("gallery")
                .delete()
                .eq("id", item_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"delete_gallery_item failed: {e}", exc_info=True)
            return False

    # ==================
    # TIME SLOTS
    # ==================

    def create_time_slot(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new time slot"""
        try:
            res = self.client.table("time_slots").insert(data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_time_slot failed: {e}", exc_info=True)
            return None

    def get_time_slot(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Get time slot by ID"""
        try:
            res = (
                self.client.table("time_slots")
                .select("*")
                .eq("id", slot_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_time_slot failed: {e}", exc_info=True)
            return None

    def get_time_slots_by_date(self, date_obj: date) -> List[Dict[str, Any]]:
        """Get time slots for a specific date"""
        try:
            res = (
                self.client.table("time_slots")
                .select("*")
                .eq("date", date_obj.isoformat())
                .order("start_time")
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"get_time_slots_by_date failed: {e}", exc_info=True)
            return []

    def get_available_slots(self, date_obj: date) -> List[Dict[str, Any]]:
        """Get available time slots for a date"""
        try:
            slots = self.get_time_slots_by_date(date_obj)
            available_slots = []
            
            for slot in slots:
                max_capacity = slot.get('max_capacity', settings.MAX_APPOINTMENTS_PER_SLOT)
                current_bookings = slot.get('current_bookings', 0)
                available_spots = max_capacity - current_bookings
                
                slot_info = {
                    **slot,
                    'available_spots': available_spots,
                    'is_available': available_spots > 0
                }
                available_slots.append(slot_info)
            
            return available_slots
        except Exception as e:
            logger.error(f"get_available_slots failed: {e}", exc_info=True)
            return []

    def increment_time_slot_bookings(self, slot_id: str) -> bool:
        """Increment bookings count for a time slot"""
        try:
            slot = self.get_time_slot(slot_id)
            if not slot:
                return False
            
            new_count = slot.get('current_bookings', 0) + 1
            res = (
                self.client.table("time_slots")
                .update({'current_bookings': new_count, 'updated_at': datetime.utcnow().isoformat()})
                .eq("id", slot_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"increment_time_slot_bookings failed: {e}", exc_info=True)
            return False

    def decrement_time_slot_bookings(self, slot_id: str) -> bool:
        """Decrement bookings count for a time slot"""
        try:
            slot = self.get_time_slot(slot_id)
            if not slot:
                return False
            
            new_count = max(0, slot.get('current_bookings', 0) - 1)
            res = (
                self.client.table("time_slots")
                .update({'current_bookings': new_count, 'updated_at': datetime.utcnow().isoformat()})
                .eq("id", slot_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"decrement_time_slot_bookings failed: {e}", exc_info=True)
            return False

    def generate_time_slots_for_date(
        self,
        date_obj: date,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Generate time slots for a specific date"""
        try:
            # Check if slots already exist for this date
            existing_slots = self.get_time_slots_by_date(date_obj)
            if existing_slots:
                logger.info(f"Time slots already exist for {date_obj}")
                return existing_slots
            
            # Parse working hours
            start_hour, start_minute = map(int, settings.WORKING_HOURS_START.split(':'))
            end_hour, end_minute = map(int, settings.WORKING_HOURS_END.split(':'))
            
            current_time = datetime.combine(date_obj, time(start_hour, start_minute))
            end_time = datetime.combine(date_obj, time(end_hour, end_minute))
            
            slots = []
            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                if slot_end <= end_time:
                    slot_data = {
                        'date': date_obj.isoformat(),
                        'start_time': current_time.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'max_capacity': settings.MAX_APPOINTMENTS_PER_SLOT,
                        'current_bookings': 0,
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    created_slot = self.create_time_slot(slot_data)
                    if created_slot:
                        slots.append(created_slot)
                
                current_time = slot_end
            
            logger.info(f"Generated {len(slots)} time slots for {date_obj}")
            return slots
            
        except Exception as e:
            logger.error(f"generate_time_slots_for_date failed: {e}", exc_info=True)
            return []

    # ==================
    # APPOINTMENTS
    # ==================

    def create_appointment(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new appointment"""
        try:
            res = self.client.table("appointments").insert(data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"create_appointment failed: {e}", exc_info=True)
            return None

    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment by ID"""
        try:
            res = (
                self.client.table("appointments")
                .select("*")
                .eq("id", appointment_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"get_appointment failed: {e}", exc_info=True)
            return None

    def get_appointments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get appointments with optional filters"""
        try:
            query = self.client.table("appointments").select("*")

            if filters:
                for k, v in filters.items():
                    if v is not None:
                        query = query.eq(k, v)

            res = (
                query.order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"get_appointments failed: {e}", exc_info=True)
            return []

    def update_appointment(self, appointment_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update appointment"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            res = (
                self.client.table("appointments")
                .update(update_data)
                .eq("id", appointment_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"update_appointment failed: {e}", exc_info=True)
            return None

    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete appointment"""
        try:
            res = (
                self.client.table("appointments")
                .delete()
                .eq("id", appointment_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error(f"delete_appointment failed: {e}", exc_info=True)
            return False

    # ==================
    # STATISTICS
    # ==================

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            # Get all orders
            orders = self.get_orders(limit=10000)
            messages = self.get_messages(limit=10000)
            appointments = self.get_appointments(limit=10000)
            
            # Calculate order statistics
            total_orders = len(orders)
            pending_orders = sum(1 for o in orders if o.get('status') == 'pending')
            completed_orders = sum(1 for o in orders if o.get('status') == 'completed')
            cancelled_orders = sum(1 for o in orders if o.get('status') == 'cancelled')
            total_revenue = sum(o.get('price', 0) for o in orders if o.get('status') == 'completed')
            
            # Calculate message statistics
            total_messages = len(messages)
            unread_messages = sum(1 for m in messages if m.get('status') == 'unread')
            
            # Calculate appointment statistics
            total_appointments = len(appointments)
            upcoming_appointments = sum(
                1 for a in appointments 
                if a.get('status') == 'confirmed'
            )
            
            return {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': total_revenue,
                'total_messages': total_messages,
                'unread_messages': unread_messages,
                'total_appointments': total_appointments,
                'upcoming_appointments': upcoming_appointments
            }
            
        except Exception as e:
            logger.error(f"get_stats failed: {e}", exc_info=True)
            return {}


# =========================
# Global instance
# =========================

db_manager = DatabaseManager()
