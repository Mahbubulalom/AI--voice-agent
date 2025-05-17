"""
Twilio voice service for making and receiving calls.
"""

import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioVoiceService:
    """
    Service for handling Twilio voice calls including making outbound calls
    and responding to incoming calls.
    """
    
    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        """
        Initialize the Twilio voice service.
        
        Args:
            account_sid (str): Twilio account SID
            auth_token (str): Twilio auth token
            phone_number (str): Twilio phone number to use for calls
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        
        # Initialize Twilio client if credentials are provided
        self.client = None
        if account_sid and auth_token:
            self.client = Client(account_sid, auth_token)
    
    def make_call(self, to_number: str, callback_url: str, status_callback_url: Optional[str] = None) -> str:
        """
        Make an outbound call.
        
        Args:
            to_number (str): Phone number to call
            callback_url (str): URL for Twilio to request TwiML instructions
            status_callback_url (str, optional): URL for call status updates
            
        Returns:
            str: Call SID
        """
        if not self.client:
            raise ValueError("Twilio client not initialized. Check your credentials.")
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=callback_url,
                status_callback=status_callback_url,
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            logger.info(f"Initiated call to {to_number}: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error making call: {str(e)}")
            raise
    
    def handle_incoming_call(self, request_data: Dict[str, Any], voice_agent) -> str:
        """
        Handle an incoming call webhook from Twilio.
        
        Args:
            request_data (Dict): Webhook data from Twilio
            voice_agent: VoiceAgent instance for generating responses
            
        Returns:
            str: TwiML response
        """
        try:
            response = VoiceResponse()
            
            # Get call information
            call_sid = request_data.get('CallSid')
            caller = request_data.get('From', 'Unknown')
            
            # Check if this is a response to a gather
            if 'SpeechResult' in request_data:
                # Process the speech input
                speech_input = request_data.get('SpeechResult', '')
                
                # Get response from the voice agent
                agent_response = voice_agent.process_voice_input(speech_input, {'call_sid': call_sid})
                
                # Say the response
                response.say(agent_response)
                
                # Gather the next input
                gather = Gather(
                    input='speech',
                    action='/voice-webhook',
                    method='POST',
                    speech_timeout='auto',
                    language='en-US'
                )
                gather.say("Is there anything else I can help you with?")
                response.append(gather)
                
                # If no input, end the call
                response.say("Thank you for calling My Dentist. Goodbye!")
                response.hangup()
            else:
                # Initial greeting
                greeting = "Thank you for calling My Dentist. I'm the automated assistant. How can I help you today?"
                
                # Gather the caller's speech input
                gather = Gather(
                    input='speech',
                    action='/voice-webhook',
                    method='POST',
                    speech_timeout='auto',
                    language='en-US'
                )
                gather.say(greeting)
                response.append(gather)
                
                # If no input, repeat the greeting
                response.say("I didn't hear anything. " + greeting)
                
                # Set up another gather
                gather = Gather(
                    input='speech',
                    action='/voice-webhook',
                    method='POST',
                    speech_timeout='auto',
                    language='en-US'
                )
                response.append(gather)
                
                # If still no input, end the call
                response.say("I didn't receive any input. Please call back when you're ready. Goodbye!")
                response.hangup()
            
            logger.info(f"Generated TwiML response for call {call_sid}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {str(e)}")
            
            # Create a simple response in case of error
            response = VoiceResponse()
            response.say("I'm sorry, there was an error processing your request. Please try again later.")
            response.hangup()
            
            return str(response)
    
    def generate_appointment_reminder_twiml(self, reminder_text: str) -> str:
        """
        Generate TwiML for an appointment reminder call.
        
        Args:
            reminder_text (str): Text to say in the reminder
            
        Returns:
            str: TwiML response
        """
        response = VoiceResponse()
        
        # Say the reminder message
        response.say(reminder_text)
        
        # Gather for confirmation
        gather = Gather(
            num_digits=1,
            action='/appointment-confirm',
            method='POST'
        )
        gather.say("Press 1 to confirm your appointment, or press 2 to speak with our staff.")
        response.append(gather)
        
        # If no input, repeat the options
        response.say("I didn't receive your input. Let me repeat.")
        
        gather = Gather(
            num_digits=1,
            action='/appointment-confirm',
            method='POST'
        )
        gather.say("Press 1 to confirm your appointment, or press 2 to speak with our staff.")
        response.append(gather)
        
        # If still no input, end the call
        response.say("Thank you for your time. If you need to make any changes to your appointment, please call our office during business hours. Goodbye!")
        response.hangup()
        
        return str(response)
    
    def handle_appointment_confirmation(self, request_data: Dict[str, Any]) -> str:
        """
        Handle appointment confirmation webhook.
        
        Args:
            request_data (Dict): Webhook data from Twilio
            
        Returns:
            str: TwiML response
        """
        response = VoiceResponse()
        
        # Get the digit pressed
        digit = request_data.get('Digits', '')
        
        if digit == '1':
            # Appointment confirmed
            response.say("Thank you for confirming your appointment. We look forward to seeing you. Goodbye!")
            response.hangup()
        elif digit == '2':
            # Transfer to staff
            response.say("I'll connect you with our office staff. Please hold.")
            # The actual transfer would typically go to a call center number
            # For this example, we'll just add a placeholder
            response.dial("+11234567890")
            response.say("The call could not be completed. Please try calling our main office number directly. Goodbye!")
            response.hangup()
        else:
            # Invalid input
            response.say("I'm sorry, I didn't understand your selection.")
            
            gather = Gather(
                num_digits=1,
                action='/appointment-confirm',
                method='POST'
            )
            gather.say("Press 1 to confirm your appointment, or press 2 to speak with our staff.")
            response.append(gather)
            
            response.say("Thank you for your time. Goodbye!")
            response.hangup()
        
        return str(response)
