# Ai Voice Agent

An AI-powered voice agent for dental practices that handles appointment reminders via phone calls and answers patient questions using a knowledge base.

## Features

- **Automated Appointment Reminders**: Make automated calls to remind patients of their upcoming appointments
- **Interactive Voice Responses**: Natural voice conversations with patients using OpenAI's advanced models
- **Knowledge Base**: Upload and search practice documents to provide accurate information to patients
- **Easy Administration**: Web interface for scheduling reminders and managing the knowledge base

## Architecture

The system uses the following key components:

- **OpenAI GPT-4o**: For natural language understanding and generation
- **Twilio**: For phone calls and voice interaction
- **LangChain**: For document processing and knowledge retrieval
- **FastAPI**: For the backend API and web server
- **SQLAlchemy**: For database interactions

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite for development)
- OpenAI API Key
- Twilio Account with Voice capabilities

### Setup

1. Clone the repository

```bash
git clone https://github.com/Mahbubulalom/my-dentist-voice-agent.git
cd my-dentist-voice-agent
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables

```bash
cp .env.example .env
# Edit the .env file with your OpenAI API key, Twilio credentials, and other settings
```

5. Run the application

```bash
python app.py
```

The application will be available at http://localhost:5000

## Configuration

Edit the `.env` file with the following settings:

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/dentist_db

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=5000
DEBUG=True
BASE_URL=your_public_url_or_ngrok_url  # For Twilio callbacks

# Knowledge Base Settings
KNOWLEDGE_BASE_DIR=knowledge_base
VECTOR_DB_PATH=vector_store
```

## Using Twilio with a Development Environment

During development, you can use tools like ngrok to expose your local server to the internet for Twilio callbacks:

```bash
ngrok http 5000
```

Then update your `.env` file with the ngrok URL:

```
BASE_URL=https://your-ngrok-url.ngrok.io
```

You'll also need to configure your Twilio number's webhook URLs to point to your ngrok URL for voice calls.

## Knowledge Base Management

Upload documents to the knowledge base through the web interface or place them directly in the `knowledge_base` directory. Supported file types:

- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)
- CSV Files (`.csv`)
- HTML Files (`.html`, `.htm`)

The system will automatically index these documents for retrieval during voice conversations.

## Making Appointment Reminder Calls

1. Navigate to the web interface at `http://localhost:5000`
2. Click "Schedule an Appointment Reminder"
3. Fill in the patient details and appointment information
4. Click "Schedule Reminder"

The system will automatically call the patient at the appropriate time (default is 24 hours before the appointment).

## Voice Agent Capabilities

The voice agent can:

- Answer questions about dental procedures
- Provide information about the practice
- Handle appointment confirmations
- Transfer calls to staff when needed

## Development

### Project Structure

```
my-dentist-voice-agent/
├── app.py                   # Main application entry point
├── requirements.txt         # Dependencies
├── .env.example             # Example environment variables
├── static/                  # Static web files
│   └── index.html           # Web interface
├── src/                     # Source code
│   ├── agents/              # Voice agent implementation
│   ├── api/                 # API routes
│   ├── appointments/        # Appointment reminder service
│   ├── database/            # Database models and connection
│   ├── knowledge/           # Knowledge base implementation
│   └── voice/               # Twilio voice services
└── knowledge_base/          # Uploaded documents
```

### Extending the Voice Agent

To extend the agent's capabilities, modify the system prompts in `src/agents/voice_agent.py` to include more information about your dental practice.

## Deployment

For production deployment:

1. Set up a proper PostgreSQL database
2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```
3. Set `DEBUG=False` in your `.env` file
4. Use a reverse proxy like Nginx in front of the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
