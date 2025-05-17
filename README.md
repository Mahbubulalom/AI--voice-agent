# My Dentist Voice Agent

A voice agent for dental practices that handles appointment reminders and knowledge-based inquiries using OpenAI's models.

## Features

- **Appointment Reminders**: Automated calls to remind patients about upcoming appointments
- **Knowledge Base**: Answer patient questions using uploaded dental practice information
- **Voice Interaction**: Natural voice conversations with patients

## Installation

```bash
# Clone the repository
git clone https://github.com/Mahbubulalom/my-dentist-voice-agent.git
cd my-dentist-voice-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit the .env file with your API keys and configuration
```

## Usage

```bash
# Run the application
python app.py
```

## Knowledge Base Management

Upload your dental practice documents to the `knowledge_base` directory. The agent will automatically index and use this information to answer patient inquiries.

## Configuration

Configure your agent in the `.env` file including:
- OpenAI API keys
- Voice settings
- Appointment database connection
- Phone service credentials
