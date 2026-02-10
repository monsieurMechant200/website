from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models import MessageCreate, MessageInDB, MessageUpdate
from app.schemas import MessageFilter, PaginationParams
from app.auth import auth_handler
from app.crud import crud_handler

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.post("/", response_model=MessageInDB)
async def create_message(message: MessageCreate):
    """Create a new contact message"""
    created_message = await crud_handler.create_message(message)
    
    if not created_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )
    
    return created_message

@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get all messages (admin only)"""
    messages = await crud_handler.get_messages(
        skip=(pagination.page - 1) * pagination.limit,
        limit=pagination.limit,
        status=status
    )
    
    return messages

@router.get("/{message_id}", response_model=MessageInDB)
async def get_message(
    message_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get message by ID (admin only)"""
    # In Supabase, we need to implement get_message_by_id
    # For now, we'll filter from all messages
    messages = await crud_handler.get_messages()
    message = next((m for m in messages if m.get('id') == message_id), None)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message

@router.put("/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Mark message as read (admin only)"""
    updated_message = await crud_handler.mark_message_as_read(message_id)
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {"message": "Message marked as read", "data": updated_message}

@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Delete message (admin only)"""
    # We need to implement delete_message in crud
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete message not implemented yet"
    )

@router.get("/stats/summary")
async def get_messages_summary(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get messages summary statistics (admin only)"""
    try:
        messages = await crud_handler.get_messages()
        
        if not messages:
            return {
                "total": 0,
                "unread": 0,
                "read": 0,
                "today": 0
            }
        
        total = len(messages)
        unread = sum(1 for m in messages if m.get('status') == 'unread')
        read = total - unread
        
        # Count messages from today
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        today_count = sum(1 for m in messages 
                         if datetime.fromisoformat(m.get('created_at', '')).date() == today)
        
        return {
            "total": total,
            "unread": unread,
            "read": read,
            "today": today_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )