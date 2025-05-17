"""
Appointment reminder service responsible for scheduling and making reminder calls.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from src.database.models import AppointmentReminder
from src.voice.twilio_service import TwilioVoiceService
from src.agents.voice_agent import VoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentService:
    """
    Service for managing appointment reminders and scheduling calls.
    """
    
    def __init__(self, voice_agent: VoiceAgent, twilio_service: TwilioVoiceService):
        """
        Initialize the appointment service.
        
        Args:
            voice_agent (VoiceAgent): Voice agent instance
            twilio_service (TwilioVoiceService): Twilio service instance
        """
        self.voice_agent = voice_agent
        self.twilio_service = twilio_service
        
        # Base URL for callbacks
        self.base_url = os.getenv("BASE_URL", "http://localhost:5000")
    
    def create_appointment_reminder(self, 
                                   db: Session,
                                   phone_number: str,
                                   appointment_date: str,
                                   patient_name: str,
                                   message: Optional[str] = None) -> int:
        """
        Create a new appointment reminder in the database.
        
        Args:
            db (Session): Database session
            phone_number (str): Patient's phone number
            appointment_date (str): Appointment date and time (ISO format)
            patient_name (str): Patient's name
            message (str, optional): Custom message for the reminder
            
        Returns:
            int: Reminder ID
        """
        try:
            # Parse appointment date
            appointment_datetime = datetime.fromisoformat(appointment_date)
            
            # Create reminder object
            reminder = AppointmentReminder(
                patient_name=patient_name,
                phone_number=phone_number,
                appointment_date=appointment_datetime,
                message=message,
                status="scheduled"
            )
            
            # Add to database
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            
            logger.info(f"Created appointment reminder for {patient_name} on {appointment_date}")
            
            return reminder.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating appointment reminder: {str(e)}")
            raise
    
    def schedule_reminder_call(self, reminder_id: int, db: Session):
        """
        Schedule a reminder call for the specified reminder.
        
        Args:
            reminder_id (int): Reminder ID
            db (Session): Database session
        """
        try:
            # Get reminder from database
            reminder = db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
            
            if not reminder:
                logger.error(f"Reminder with ID {reminder_id} not found")
                return
            
            # Get appointment date
            appointment_date = reminder.appointment_date
            
            # Schedule call for 24 hours before the appointment
            call_time = appointment_date - timedelta(hours=24)
            
            # If the appointment is less than 24 hours away, schedule for now
            if call_time < datetime.utcnow():
                self._make_reminder_call(reminder, db)
            else:
                # In a production system, you would use a job scheduler
                # like Celery to schedule the call at the appropriate time
                logger.info(f"Would schedule call for {call_time} for reminder {reminder_id}")
                
        except Exception as e:
            logger.error(f"Error scheduling reminder call: {str(e)}")
    
    def _make_reminder_call(self, reminder: AppointmentReminder, db: Session):
        """
        Make a reminder call for the specified reminder.
        
        Args:
            reminder (AppointmentReminder): Reminder object
            db (Session): Database session
        """
        try:
            # Get reminder text from voice agent
            reminder_text = self.voice_agent.get_appointment_reminder(
                patient_name=reminder.patient_name,
                appointment_date=reminder.appointment_date.strftime("%A, %B %d at %I:%M %p"),
                custom_message=reminder.message
            )
            
            # Generate TwiML for the call
            twiml = self.twilio_service.generate_appointment_reminder_twiml(reminder_text)
            
            # Callback URL for when the call is answered
            callback_url = f"{self.base_url}/appointment-reminder-twiml/{reminder.id}"
            
            # Status callback URL
            status_callback_url = f"{self.base_url}/call-status-callback/{reminder.id}"
            
            # Make the call
            call_sid = self.twilio_service.make_call(
                to_number=reminder.phone_number,
                callback_url=callback_url,
                status_callback_url=status_callback_url
            )
            
            # Update reminder with call SID and status
            reminder.call_sid = call_sid
            reminder.status = "sent"
            db.commit()
            
            logger.info(f"Made reminder call to {reminder.phone_number} for reminder {reminder.id}")
            
        except Exception as e:
            # Update reminder status to failed
            reminder.status = "failed"
            db.commit()
            
            logger.error(f"Error making reminder call: {str(e)}")
    
    def handle_call_status_callback(self, call_sid: str, status: str, db: Session):
        """
        Handle call status callbacks from Twilio.
        
        Args:
            call_sid (str): Call SID
            status (str): Call status
            db (Session): Database session
        """
        try:
            # Find reminder by call SID
            reminder = db.query(AppointmentReminder).filter(AppointmentReminder.call_sid == call_sid).first()
            
            if not reminder:
                logger.warning(f"No reminder found for call SID {call_sid}")
                return
            
            # Update status based on call status
            if status == "completed":
                reminder.status = "sent"
            elif status == "failed" or status == "busy" or status == "no-answer":
                reminder.status = "failed"
                
            db.commit()
            
            logger.info(f"Updated status for reminder {reminder.id} to {reminder.status}")
            
        except Exception as e:
            logger.error(f"Error handling call status callback: {str(e)}")
    
    def handle_appointment_confirmation(self, reminder_id: int, confirmed: bool, db: Session):
        """
        Handle appointment confirmation from the patient.
        
        Args:
            reminder_id (int): Reminder ID
            confirmed (bool): Whether the appointment was confirmed
            db (Session): Database session
        """
        try:
            # Find reminder
            reminder = db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
            
            if not reminder:
                logger.warning(f"No reminder found with ID {reminder_id}")
                return
            
            # Update status based on confirmation
            if confirmed:
                reminder.status = "confirmed"
            else:
                reminder.status = "rescheduled"
                
            db.commit()
            
            logger.info(f"Updated status for reminder {reminder.id} to {reminder.status}")
            
        except Exception as e:
            logger.error(f"Error handling appointment confirmation: {str(e)}")
    
    def get_upcoming_reminders(self, db: Session, limit: int = 10):
        """
        Get upcoming appointment reminders.
        
        Args:
            db (Session): Database session
            limit (int): Maximum number of reminders to return
            
        Returns:
            List[AppointmentReminder]: List of upcoming reminders
        """
        try:
            # Get reminders with appointment date in the future
            now = datetime.utcnow()
            reminders = db.query(AppointmentReminder)\
                .filter(AppointmentReminder.appointment_date > now)\
                .order_by(AppointmentReminder.appointment_date)\
                .limit(limit)\
                .all()
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting upcoming reminders: {str(e)}")
            return []
