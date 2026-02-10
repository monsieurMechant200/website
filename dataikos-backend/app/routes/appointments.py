from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date, datetime
from app.models import (
    AppointmentCreate, AppointmentInDB, AppointmentUpdate,
    AvailableSlotResponse, TimeSlotCreate, TimeSlotInDB
)
from app.auth import auth_handler
from app.crud import crud_handler
from app.utils.supabase_client import db_manager

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

@router.get("/available-slots")
async def get_available_slots(
    target_date: date = Query(..., description="Date for available slots"),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get available time slots for a specific date (admin only)"""
    try:
        slots = await crud_handler.get_available_slots(target_date)
        
        # Format response
        available_slots = []
        for slot in slots:
            available_slots.append(AvailableSlotResponse(
                date=datetime.fromisoformat(slot['date']).date(),
                start_time=slot['start_time'],
                end_time=slot['end_time'],
                available_spots=slot.get('available_spots', 0),
                is_available=slot.get('is_available', False)
            ))
        
        return available_slots
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available slots: {str(e)}"
        )

@router.post("/", response_model=AppointmentInDB)
async def create_appointment(
    appointment: AppointmentCreate,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Create a new appointment (admin only)"""
    try:
        created_appointment = await crud_handler.create_appointment(appointment)
        
        if not created_appointment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create appointment. Time slot may be full."
            )
        
        return created_appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating appointment: {str(e)}"
        )

@router.get("/", response_model=List[AppointmentInDB])
async def get_appointments(
    date_filter: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get all appointments (admin only)"""
    try:
        # This would need custom implementation in db_manager
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting appointments: {str(e)}"
        )

@router.get("/{appointment_id}", response_model=AppointmentInDB)
async def get_appointment(
    appointment_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get appointment by ID (admin only)"""
    try:
        appointment = await db_manager.get_appointment(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        return appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting appointment: {str(e)}"
        )

@router.put("/{appointment_id}", response_model=AppointmentInDB)
async def update_appointment(
    appointment_id: str,
    appointment_update: AppointmentUpdate,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Update appointment (admin only)"""
    try:
        update_data = appointment_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        updated = await db_manager.update_appointment(appointment_id, update_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        return updated
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating appointment: {str(e)}"
        )

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Cancel appointment (admin only)"""
    try:
        success = await crud_handler.cancel_appointment(appointment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or already cancelled"
            )
        return {"message": "Appointment cancelled successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling appointment: {str(e)}"
        )

@router.post("/generate-slots")
async def generate_time_slots(
    start_date: date,
    end_date: date,
    service_duration: int = Query(60, ge=15, le=240),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Generate time slots for a date range (admin only)"""
    try:
        slots = await crud_handler.generate_slots_for_date_range(
            start_date, end_date, service_duration
        )
        
        return {
            "message": f"Generated {len(slots)} time slots",
            "start_date": start_date,
            "end_date": end_date,
            "slots_generated": len(slots)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating time slots: {str(e)}"
        )

@router.get("/today")
async def get_today_appointments(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get today's appointments (admin only)"""
    try:
        today = date.today()
        # This would need custom implementation
        return {"appointments": [], "date": today.isoformat()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting today's appointments: {str(e)}"
        )

@router.post("/{appointment_id}/send-reminder")
async def send_appointment_reminder(
    appointment_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Send reminder for specific appointment (admin only)"""
    try:
        appointment = await db_manager.get_appointment(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Get time slot for appointment details
        time_slot = await db_manager.get_time_slot(appointment['time_slot_id'])
        
        # Send reminder email
        success = email_service.send_appointment_reminder(
            to_email=appointment['client_email'],
            client_name=appointment['client_name'],
            appointment_date=time_slot.get('date', 'N/A'),
            appointment_time=time_slot.get('start_time', 'N/A'),
            service=appointment.get('service', 'Service'),
            price=0,  # Would need to get from order
            notes=appointment.get('notes')
        )
        
        if success:
            # Mark reminder as sent
            await db_manager.update_appointment(
                appointment_id,
                {'reminder_sent': True, 'updated_at': datetime.utcnow().isoformat()}
            )
            
        return {
            "success": success,
            "message": "Reminder sent successfully" if success else "Failed to send reminder"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending reminder: {str(e)}"
        )