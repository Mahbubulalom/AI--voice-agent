"""
Database models for the application.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.database.database import Base

class AppointmentReminder(Base):
    """
    Model for storing appointment reminders.
    """
    __tablename__ = "appointment_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(Enum('scheduled', 'sent', 'confirmed', 'rescheduled', 'failed', name='reminder_status'), 
                   default='scheduled')
    call_sid = Column(String(50), nullable=True)  # Twilio Call SID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "phone_number": self.phone_number,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "message": self.message,
            "status": self.status,
            "call_sid": self.call_sid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Document(Base):
    """
    Model for tracking uploaded documents in the knowledge base.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), unique=True, index=True, nullable=False)  # UUID generated for the document
    filename = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "filename": self.filename,
            "description": self.description,
            "file_type": self.file_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class CallLog(Base):
    """
    Model for logging call interactions.
    """
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(50), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    direction = Column(Enum('inbound', 'outbound', name='call_direction'), nullable=False)
    status = Column(String(20), nullable=False)
    duration = Column(Integer, nullable=True)  # Call duration in seconds
    recording_url = Column(String(255), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Relationship to call transcripts
    transcripts = relationship("CallTranscript", back_populates="call")
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "call_sid": self.call_sid,
            "phone_number": self.phone_number,
            "direction": self.direction,
            "status": self.status,
            "duration": self.duration,
            "recording_url": self.recording_url,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

class CallTranscript(Base):
    """
    Model for storing call transcripts and interactions.
    """
    __tablename__ = "call_transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("call_logs.id"))
    speaker = Column(Enum('system', 'user', name='transcript_speaker'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to call log
    call = relationship("CallLog", back_populates="transcripts")
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "call_id": self.call_id,
            "speaker": self.speaker,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
