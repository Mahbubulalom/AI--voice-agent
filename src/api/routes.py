"""
API routes for the application.
"""

import os
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import AppointmentReminder
from src.appointments.appointment_service import AppointmentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

@router.get("/api/reminders", response_model=Dict[str, List[Dict[str, Any]]])
async def get_reminders(db: Session = Depends(get_db)):
    """
    Get all appointment reminders.
    """
    try:
        reminders = db.query(AppointmentReminder).order_by(AppointmentReminder.appointment_date.desc()).limit(10).all()
        return {"reminders": [reminder.to_dict() for reminder in reminders]}
    except Exception as e:
        logger.error(f"Error getting reminders: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving reminders")

@router.get("/api/reminders/{reminder_id}", response_model=Dict[str, Any])
async def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """
    Get a specific appointment reminder.
    """
    try:
        reminder = db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        return {"reminder": reminder.to_dict()}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting reminder: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving reminder")

@router.get("/appointment-reminder-twiml/{reminder_id}")
async def get_appointment_reminder_twiml(reminder_id: int, voice_agent, twilio_service, db: Session = Depends(get_db)):
    """
    Generate TwiML for an appointment reminder call.
    """
    try:
        reminder = db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        
        # Get reminder text from voice agent
        reminder_text = voice_agent.get_appointment_reminder(
            patient_name=reminder.patient_name,
            appointment_date=reminder.appointment_date.strftime("%A, %B %d at %I:%M %p"),
            custom_message=reminder.message
        )
        
        # Generate TwiML
        twiml = twilio_service.generate_appointment_reminder_twiml(reminder_text)
        
        return twiml
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating TwiML: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating TwiML")

@router.post("/call-status-callback/{reminder_id}")
async def call_status_callback(reminder_id: int, appointment_service: AppointmentService, db: Session = Depends(get_db)):
    """
    Handle Twilio call status callbacks.
    """
    try:
        reminder = db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        
        # Update reminder status based on call status
        appointment_service.handle_call_status_callback(reminder.call_sid, "completed", db)
        
        return {"message": "Status updated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error handling call status callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Error handling call status callback")

@router.post("/appointment-confirm")
async def appointment_confirm(appointment_service: AppointmentService, db: Session = Depends(get_db)):
    """
    Handle appointment confirmation responses.
    """
    try:
        # In a real implementation, this would parse the Twilio request
        # and extract the digit pressed and the call SID
        digit_pressed = "1"  # Example: 1 for confirm, 2 for reschedule
        call_sid = "example_call_sid"
        
        # Find reminder by call SID
        reminder = db.query(AppointmentReminder).filter(AppointmentReminder.call_sid == call_sid).first()
        if not reminder:
            raise HTTPException(status_code=404, detail=f"No reminder found for call SID {call_sid}")
        
        # Handle confirmation
        confirmed = digit_pressed == "1"
        appointment_service.handle_appointment_confirmation(reminder.id, confirmed, db)
        
        # Return appropriate TwiML
        if confirmed:
            return {"message": "Appointment confirmed"}
        else:
            return {"message": "Appointment rescheduling requested"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error confirming appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error confirming appointment")

@router.get("/api/documents")
async def get_documents(db: Session = Depends(get_db)):
    """
    Get all documents in the knowledge base.
    """
    try:
        from src.database.models import Document
        documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
        return {"documents": [document.to_dict() for document in documents]}
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}
