import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz

from app.utils.supabase_client import db_manager
from app.utils.email_service import email_service
from app.config import settings

logger = logging.getLogger(__name__)

class AppointmentScheduler:
    """Scheduler for appointment reminders"""
    
    def __init__(self):
        self.is_running = False
        self.timezone = pytz.timezone('Africa/Douala')  # Cameroon timezone
    
    async def check_reminders(self):
        """Check and send reminders for appointments in 24 hours"""
        try:
            # Calculate target time (24 hours from now)
            now = datetime.now(self.timezone)
            target_time = now + timedelta(hours=settings.APPOINTMENT_REMINDER_HOURS)
            
            # Format dates for query
            target_date = target_time.date()
            target_hour = target_time.hour
            
            logger.info(f"Checking reminders for {target_date} around {target_hour}:00")
            
            # Get appointments for the target date
            # Note: This requires implementing a method in db_manager
            # We'll get all appointments and filter locally for now
            
            appointments = await self._get_upcoming_appointments()
            
            for appointment in appointments:
                if not appointment.get('reminder_sent', False):
                    # Check if appointment is ~24 hours away
                    appointment_time = self._parse_appointment_time(appointment)
                    if appointment_time:
                        time_diff = appointment_time - now
                        
                        # If appointment is between 23 and 25 hours from now
                        if timedelta(hours=23) < time_diff < timedelta(hours=25):
                            await self._send_reminder(appointment)
            
            logger.info(f"Reminder check completed at {now}")
            
        except Exception as e:
            logger.error(f"Error in reminder check: {e}")
    
    async def _get_upcoming_appointments(self) -> List[Dict[str, Any]]:
        """Get upcoming appointments that need reminders"""
        try:
            # Get appointments from the next 2 days
            # This is a simplified version - in production, use a proper query
            
            # First get all appointments with their time slots
            appointments = []
            
            # Query logic will depend on your database structure
            # For now, return empty list
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {e}")
            return []
    
    def _parse_appointment_time(self, appointment: Dict[str, Any]) -> Optional[datetime]:
        """Parse appointment date and time to datetime object"""
        try:
            # This depends on how you store appointment times
            # Adjust based on your data structure
            return None
        except Exception as e:
            logger.error(f"Error parsing appointment time: {e}")
            return None
    
    async def _send_reminder(self, appointment: Dict[str, Any]):
        """Send reminder email and update appointment"""
        try:
            # Send email
            success = email_service.send_appointment_reminder(
                to_email=appointment['client_email'],
                client_name=appointment['client_name'],
                appointment_date=appointment.get('appointment_date', 'N/A'),
                appointment_time=appointment.get('appointment_time', 'N/A'),
                service=appointment.get('service', 'Service'),
                price=appointment.get('price', 0),
                notes=appointment.get('notes')
            )
            
            if success:
                # Mark reminder as sent
                await db_manager.update_appointment(
                    appointment['id'],
                    {'reminder_sent': True}
                )
                logger.info(f"Reminder sent for appointment {appointment['id']}")
            else:
                logger.warning(f"Failed to send reminder for appointment {appointment['id']}")
                
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
    
    async def start(self):
        """Start the scheduler"""
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled")
            return
        
        self.is_running = True
        logger.info("Starting appointment scheduler")
        
        while self.is_running:
            try:
                await self.check_reminders()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            # Wait for the next check interval
            await asyncio.sleep(settings.SCHEDULER_CHECK_INTERVAL * 60)
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Stopping appointment scheduler")

# Global scheduler instance
scheduler = AppointmentScheduler()