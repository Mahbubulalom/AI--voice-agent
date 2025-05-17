"""
Main application file for the My Dentist Voice Agent.
This handles the web server and API endpoints.
"""

import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session

from src.database.database import get_db, engine, Base
from src.knowledge.knowledge_base import KnowledgeBase
from src.voice.twilio_service import TwilioVoiceService
from src.appointments.appointment_service import AppointmentService
from src.agents.voice_agent import VoiceAgent

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="My Dentist Voice Agent",
    description="A voice agent for dental practices that handles appointment reminders and answers patient inquiries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
knowledge_base = KnowledgeBase(
    os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base"),
    os.getenv("VECTOR_DB_PATH", "vector_store")
)

twilio_service = TwilioVoiceService(
    account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    phone_number=os.getenv("TWILIO_PHONE_NUMBER")
)

voice_agent = VoiceAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name=os.getenv("MODEL_NAME", "gpt-4o"),
    knowledge_base=knowledge_base
)

appointment_service = AppointmentService(
    voice_agent=voice_agent,
    twilio_service=twilio_service
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None)
):
    """Upload a document to the knowledge base."""
    try:
        # Save the file temporarily
        file_path = f"knowledge_base/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Add to knowledge base
        document_id = knowledge_base.add_document(file_path, description)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Document added successfully", "document_id": document_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule-reminder")
async def schedule_reminder(
    background_tasks: BackgroundTasks,
    phone_number: str = Form(...),
    appointment_date: str = Form(...),
    patient_name: str = Form(...),
    message: str = Form(None),
    db: Session = Depends(get_db)
):
    """Schedule an appointment reminder call."""
    try:
        reminder_id = appointment_service.create_appointment_reminder(
            db=db,
            phone_number=phone_number,
            appointment_date=appointment_date,
            patient_name=patient_name,
            message=message
        )
        
        # Schedule the call in the background
        background_tasks.add_task(
            appointment_service.schedule_reminder_call,
            reminder_id=reminder_id,
            db=db
        )
        
        return JSONResponse(
            status_code=200,
            content={"message": "Reminder scheduled successfully", "reminder_id": reminder_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-webhook")
async def voice_webhook(request_data: dict):
    """Handle Twilio voice webhook."""
    try:
        response = twilio_service.handle_incoming_call(request_data, voice_agent)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Run the application
if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run("app:app", host=host, port=port, reload=debug)
