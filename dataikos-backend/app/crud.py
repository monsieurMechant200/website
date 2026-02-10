from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from app.utils.supabase_client import db_manager
from app.utils.email_service import email_service
from app.models import (
    OrderCreate,
    MessageCreate,
    GalleryItemCreate,
    AppointmentCreate
)

logger = logging.getLogger(__name__)


class CRUDHandler:
    """
    Centralized CRUD & business logic handler.
    Designed for SaaS production usage.
    """

    # ==========================
    # ORDERS
    # ==========================

    @staticmethod
    async def create_order(order_data: OrderCreate) -> Optional[Dict[str, Any]]:
        """
        Create a new order.
        Optionally creates an appointment if a time slot is provided.
        """
        try:
            order_dict = order_data.model_dump()
            now = datetime.utcnow().isoformat()

            order_dict.update({
                "created_at": now,
                "updated_at": now,
                "status": "pending"
            })

            order = db_manager.create_order(order_dict)
            if not order:
                return None

            # Create appointment if time slot exists
            if order_data.time_slot_id:
                appointment_data = AppointmentCreate(
                    order_id=order["id"],
                    time_slot_id=order_data.time_slot_id,
                    client_email=order_data.client_email,
                    client_name=order_data.client_name,
                    client_phone=order_data.client_phone,
                    service=order_data.service,
                    notes=order_data.client_description
                )

                appointment = await CRUDHandler.create_appointment(appointment_data)
                if appointment:
                    db_manager.update_order(
                        order["id"],
                        {"appointment_id": appointment["id"]}
                    )
                    order["appointment_id"] = appointment["id"]

            return order

        except Exception as e:
            logger.exception("Error creating order")
            return None

    @staticmethod
    async def get_orders(
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get orders with optional status filter"""
        try:
            filters = {}
            if status:
                filters["status"] = status

            return db_manager.get_orders(filters, limit, skip)

        except Exception as e:
            logger.exception("Error fetching orders")
            return []

    @staticmethod
    async def update_order_status(
        order_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update order status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if notes:
                update_data["admin_notes"] = notes

            return db_manager.update_order(order_id, update_data)

        except Exception as e:
            logger.exception("Error updating order status")
            return None

    @staticmethod
    async def delete_order(order_id: str) -> bool:
        """Delete order"""
        try:
            return db_manager.delete_order(order_id)
        except Exception:
            logger.exception("Error deleting order")
            return False

    # ==========================
    # APPOINTMENTS
    # ==========================

    @staticmethod
    async def create_appointment(
        appointment_data: AppointmentCreate
    ) -> Optional[Dict[str, Any]]:
        """
        Create appointment with capacity check and email confirmation.
        Includes rollback protection.
        """
        try:
            time_slot = db_manager.get_time_slot(
                appointment_data.time_slot_id
            )
            if not time_slot:
                logger.warning("Time slot not found")
                return None

            max_capacity = time_slot.get("max_capacity", 5)
            current_bookings = time_slot.get("current_bookings", 0)

            if current_bookings >= max_capacity:
                logger.warning("Time slot fully booked")
                return None

            now = datetime.utcnow().isoformat()
            appointment_dict = appointment_data.model_dump()
            appointment_dict.update({
                "created_at": now,
                "updated_at": now,
                "status": "confirmed"
            })

            appointment = db_manager.create_appointment(appointment_dict)
            if not appointment:
                return None

            if not db_manager.increment_time_slot_bookings(
                appointment_data.time_slot_id
            ):
                db_manager.delete_appointment(appointment["id"])
                return None

            # Send confirmation email (non-blocking)
            try:
                email_service.send_appointment_confirmation(
                    to_email=appointment_data.client_email,
                    client_name=appointment_data.client_name,
                    appointment_date=time_slot.get("date"),
                    appointment_time=time_slot.get("start_time"),
                    service=appointment_data.service,
                    price=0,
                    notes=appointment_data.notes
                )
            except Exception:
                logger.warning("Appointment created but email failed")

            return appointment

        except Exception:
            logger.exception("Error creating appointment")
            return None

    @staticmethod
    async def cancel_appointment(appointment_id: str) -> bool:
        """Cancel appointment"""
        try:
            appointment = db_manager.get_appointment(appointment_id)
            if not appointment:
                return False

            updated = db_manager.update_appointment(
                appointment_id,
                {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            if not updated:
                return False

            return db_manager.decrement_time_slot_bookings(
                appointment["time_slot_id"]
            )

        except Exception:
            logger.exception("Error cancelling appointment")
            return False

    @staticmethod
    async def get_available_slots(date_obj: date) -> List[Dict[str, Any]]:
        """Get available time slots for a date"""
        try:
            return db_manager.get_available_slots(date_obj)
        except Exception:
            logger.exception("Error fetching available slots")
            return []

    @staticmethod
    async def generate_slots_for_date_range(
        start_date: date,
        end_date: date,
        service_duration: int = 60
    ) -> List[Dict[str, Any]]:
        """Generate time slots for a date range"""
        try:
            slots = []
            current_date = start_date

            while current_date <= end_date:
                daily_slots = db_manager.generate_time_slots_for_date(
                    current_date,
                    service_duration
                )
                slots.extend(daily_slots)
                current_date += timedelta(days=1)

            return slots

        except Exception:
            logger.exception("Error generating time slots")
            return []

    # ==========================
    # MESSAGES
    # ==========================

    @staticmethod
    async def create_message(
        message_data: MessageCreate
    ) -> Optional[Dict[str, Any]]:
        """Create new message"""
        try:
            message_dict = message_data.model_dump()
            message_dict["created_at"] = datetime.utcnow().isoformat()
            message_dict["status"] = "unread"

            return db_manager.create_message(message_dict)

        except Exception:
            logger.exception("Error creating message")
            return None

    @staticmethod
    async def get_messages(
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages with optional status filter"""
        try:
            filters = {}
            if status:
                filters["status"] = status

            return db_manager.get_messages(filters, limit, skip)

        except Exception:
            logger.exception("Error fetching messages")
            return []

    @staticmethod
    async def mark_message_as_read(
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """Mark message as read"""
        try:
            return db_manager.update_message(
                message_id,
                {
                    "status": "read",
                    "read_at": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            logger.exception("Error marking message as read")
            return None

    @staticmethod
    async def delete_message(message_id: str) -> bool:
        """Delete message"""
        try:
            return db_manager.delete_message(message_id)
        except Exception:
            logger.exception("Error deleting message")
            return False

    # ==========================
    # GALLERY
    # ==========================

    @staticmethod
    async def create_gallery_item(
        item_data: GalleryItemCreate
    ) -> Optional[Dict[str, Any]]:
        """Create new gallery item"""
        try:
            item_dict = item_data.model_dump()
            item_dict["created_at"] = datetime.utcnow().isoformat()

            return db_manager.create_gallery_item(item_dict)

        except Exception:
            logger.exception("Error creating gallery item")
            return None

    @staticmethod
    async def get_gallery_items(
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get gallery items with optional category filter"""
        try:
            filters = {}
            if category:
                filters["category"] = category

            return db_manager.get_gallery_items(filters, limit, skip)

        except Exception:
            logger.exception("Error fetching gallery items")
            return []

    @staticmethod
    async def delete_gallery_item(item_id: str) -> bool:
        """Delete gallery item"""
        try:
            return db_manager.delete_gallery_item(item_id)
        except Exception:
            logger.exception("Error deleting gallery item")
            return False

    # ==========================
    # DASHBOARD / STATS
    # ==========================

    @staticmethod
    async def get_dashboard_stats() -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            return db_manager.get_stats()
        except Exception:
            logger.exception("Error fetching dashboard stats")
            return {}

    # ==========================
    # USERS
    # ==========================

    @staticmethod
    async def create_user(
        user_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            return db_manager.create_user(user_data)
        except Exception:
            logger.exception("Error creating user")
            return None

    @staticmethod
    async def update_user_password(
        user_id: str,
        new_password_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Update user password"""
        try:
            return db_manager.update_user(
                user_id,
                {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            logger.exception("Error updating user password")
            return None


# Global instance
crud_handler = CRUDHandler()
