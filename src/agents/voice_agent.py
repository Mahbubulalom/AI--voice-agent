"""
Voice agent that combines knowledge base information with OpenAI capabilities
to provide conversational responses.
"""

import os
import json
from typing import List, Dict, Any
import openai

class VoiceAgent:
    """
    Voice agent that handles conversational responses using OpenAI's models
    and a knowledge base.
    """
    
    def __init__(self, openai_api_key: str, model_name: str, knowledge_base):
        """
        Initialize the voice agent.
        
        Args:
            openai_api_key (str): OpenAI API key
            model_name (str): OpenAI model name to use
            knowledge_base: KnowledgeBase instance for retrieving information
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model_name = model_name
        self.knowledge_base = knowledge_base
        
        # Define system prompts
        self.DEFAULT_SYSTEM_PROMPT = """
        You are a helpful dental assistant for 'My Dentist' practice. 
        Your name is Dental Assistant. You help patients by answering their questions about 
        dental procedures, office policies, and appointment information.
        
        Be professional, friendly, and concise in your responses.
        If you don't know an answer, politely say so and offer to connect them with a human staff member.
        
        Always speak as if you're having a voice conversation. Keep responses brief and natural.
        """
        
        self.APPOINTMENT_REMINDER_PROMPT = """
        You are calling to remind a patient about their upcoming dental appointment.
        Be professional, friendly, and concise.
        
        Include the following information in your reminder:
        1. Identify yourself as calling from 'My Dentist' office
        2. Mention the patient's name
        3. State the appointment date and time
        4. Ask them to confirm if they'll attend
        5. If they confirm, thank them
        6. If they need to reschedule, tell them you'll connect them with the front desk
        
        Keep the conversation brief and natural, as if you're having a phone conversation.
        """
    
    def get_response(self, 
                     user_input: str, 
                     conversation_history: List[Dict[str, str]] = None, 
                     system_prompt: str = None) -> str:
        """
        Generate a response to the user input.
        
        Args:
            user_input (str): User's query or input
            conversation_history (List[Dict]): Previous conversation history
            system_prompt (str): Custom system prompt to use
            
        Returns:
            str: Agent's response
        """
        if conversation_history is None:
            conversation_history = []
        
        if system_prompt is None:
            system_prompt = self.DEFAULT_SYSTEM_PROMPT
        
        # Retrieve relevant information from knowledge base
        relevant_info = self.knowledge_base.query(user_input, top_k=3)
        
        # Format the retrieved information
        context_str = ""
        if relevant_info:
            context_str = "Information from dental practice knowledge base:\n"
            for i, (doc, metadata, score) in enumerate(relevant_info, 1):
                context_str += f"{i}. {doc}\n"
        
        # Prepare messages for the model
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add context if available
        if context_str:
            messages.append({
                "role": "system", 
                "content": f"Use the following information to answer the question if relevant:\n{context_str}"
            })
        
        # Add conversation history
        for message in conversation_history:
            messages.append(message)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_input})
        
        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=200  # Keep responses concise for voice
        )
        
        return response.choices[0].message.content
    
    def get_appointment_reminder(self, 
                                patient_name: str, 
                                appointment_date: str, 
                                custom_message: str = None) -> str:
        """
        Generate an appointment reminder message.
        
        Args:
            patient_name (str): Patient's name
            appointment_date (str): Appointment date and time
            custom_message (str): Optional custom message to include
            
        Returns:
            str: Appointment reminder message
        """
        # Prepare the prompt with appointment details
        prompt = f"""
        You're calling to remind {patient_name} about their dental appointment on {appointment_date}.
        """
        
        if custom_message:
            prompt += f"\nAdditional information: {custom_message}"
        
        messages = [
            {"role": "system", "content": self.APPOINTMENT_REMINDER_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=200  # Keep responses concise for voice
        )
        
        return response.choices[0].message.content
    
    def process_voice_input(self, text_input: str, call_metadata: Dict[str, Any] = None) -> str:
        """
        Process input from a voice call and generate a response.
        
        Args:
            text_input (str): Transcribed text from the call
            call_metadata (Dict): Additional call metadata
            
        Returns:
            str: Response to be converted to speech
        """
        # Initialize conversation or get history if exists
        conversation_id = None
        conversation_history = []
        
        if call_metadata and 'conversation_id' in call_metadata:
            conversation_id = call_metadata['conversation_id']
            # Here you could retrieve conversation history from a database
            # For simplicity, we're not implementing persistence in this example
        
        # Get response
        response = self.get_response(text_input, conversation_history)
        
        return response
