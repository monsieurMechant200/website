from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date

from app.models import OrderCreate, OrderInDB, OrderUpdate
from app.schemas import PaginationParams
from app.auth import auth_handler
from app.utils.supabase_client import db_manager

router = APIRouter(prefix="/api/orders", tags=["orders"])


# =========================
# CREATE ORDER
# =========================

@router.post("/", response_model=OrderInDB)
def create_order(order: OrderCreate):
    """Create a new order with optional appointment"""

    # Validate time slot if provided
    if order.time_slot_id:
        time_slot = db_manager.get_time_slot(order.time_slot_id)

        if not time_slot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot not found"
            )

        available = (
            time_slot.get("max_capacity", 5)
            - time_slot.get("current_bookings", 0)
        )

        if available <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot is fully booked"
            )

    created = db_manager.create_order(order.model_dump())

    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

    return created


# =========================
# AVAILABLE TIME SLOTS
# =========================

@router.get("/available-slots")
def get_available_slots(
    target_date: date = Query(..., description="Date for available slots")
):
    """Get available time slots for a specific date"""

    slots = db_manager.get_available_slots(target_date)

    return [
        {
            "id": s["id"],
            "date": s["date"],
            "start_time": s["start_time"],
            "end_time": s["end_time"],
            "available_spots": s["available_spots"],
            "is_available": s["is_available"]
        }
        for s in slots if s["is_available"]
    ]


# =========================
# GET ORDERS (ADMIN)
# =========================

@router.get("/", response_model=List[OrderInDB])
def get_orders(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    return db_manager.get_orders(
        filters={"status": status_filter},
        limit=pagination.limit,
        offset=(pagination.page - 1) * pagination.limit
    )


# =========================
# GET ORDER BY ID (ADMIN)
# =========================

@router.get("/{order_id}", response_model=OrderInDB)
def get_order(
    order_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    order = db_manager.get_order_by_id(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order


# =========================
# UPDATE ORDER (ADMIN)
# =========================

@router.put("/{order_id}", response_model=OrderInDB)
def update_order(
    order_id: str,
    order_update: OrderUpdate,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    updated = db_manager.update_order(
        order_id,
        order_update.model_dump(exclude_unset=True)
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or update failed"
        )

    return updated


# =========================
# DELETE ORDER (ADMIN)
# =========================

@router.delete("/{order_id}")
def delete_order(
    order_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    success = db_manager.delete_order(order_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return {"message": "Order deleted successfully"}


# =========================
# ORDERS STATS (ADMIN)
# =========================

@router.get("/stats/summary")
def get_orders_summary(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    orders = db_manager.get_orders(limit=10_000)

    total = len(orders)
    pending = sum(o["status"] == "pending" for o in orders)
    completed = sum(o["status"] == "completed" for o in orders)
    cancelled = sum(o["status"] == "cancelled" for o in orders)
    revenue = sum(o.get("price", 0) for o in orders if o["status"] == "completed")

    return {
        "total": total,
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled,
        "revenue": revenue
    }


# =========================
# BULK UPDATE (ADMIN)
# =========================

@router.post("/bulk-update")
def bulk_update_orders(
    order_ids: List[str],
    status: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    updated = 0

    for oid in order_ids:
        if db_manager.update_order(oid, {"status": status}):
            updated += 1

    return {
        "updated": updated,
        "total": len(order_ids)
    }
