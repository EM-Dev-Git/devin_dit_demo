import openai
import os
import json
from typing import Dict, List, Optional
from modules.logger import get_logger

logger = get_logger(__name__)

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai.api_key = self.api_key
    
    def generate_minutes(self, transcript: str, meeting_title: Optional[str] = None, participants: Optional[List[str]] = None) -> Dict:
        try:
            prompt = self._create_prompt(transcript, meeting_title, participants)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert meeting minutes generator. Generate structured meeting minutes from transcripts in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI response received for transcript processing")
            
            try:
                result = json.loads(content)
                return self._validate_and_format_response(result, meeting_title, participants)
            except json.JSONDecodeError:
                logger.error("Failed to parse OpenAI response as JSON")
                return self._create_fallback_response(transcript, meeting_title, participants)
                
        except Exception as e:
            logger.error(f"Error generating minutes with OpenAI: {str(e)}")
            return self._create_fallback_response(transcript, meeting_title, participants)
    
    def _create_prompt(self, transcript: str, meeting_title: Optional[str], participants: Optional[List[str]]) -> str:
        prompt = f"""
Please analyze the following meeting transcript and generate structured meeting minutes in JSON format.

Transcript:
{transcript}

Please provide the response in the following JSON structure:
{{
    "meeting_title": "Generated or provided meeting title",
    "summary": "Brief summary of the meeting (2-3 sentences)",
    "key_points": ["List of key discussion points"],
    "action_items": ["List of action items with responsible parties if mentioned"],
    "participants": ["List of identified participants"]
}}

Requirements:
- Extract key discussion points and decisions made
- Identify action items and next steps
- List participants mentioned in the transcript
- Generate a concise but informative summary
- If no clear meeting title is provided, generate an appropriate one based on content
"""
        
        if meeting_title:
            prompt += f"\nMeeting Title: {meeting_title}"
        
        if participants:
            prompt += f"\nKnown Participants: {', '.join(participants)}"
        
        return prompt
    
    def _validate_and_format_response(self, result: Dict, meeting_title: Optional[str], participants: Optional[List[str]]) -> Dict:
        formatted_result = {
            "meeting_title": result.get("meeting_title", meeting_title or "Meeting Minutes"),
            "summary": result.get("summary", "No summary available"),
            "key_points": result.get("key_points", []) if isinstance(result.get("key_points"), list) else [],
            "action_items": result.get("action_items", []) if isinstance(result.get("action_items"), list) else [],
            "participants": result.get("participants", participants or []) if isinstance(result.get("participants"), list) else participants or []
        }
        
        return formatted_result
    
    def _create_fallback_response(self, transcript: str, meeting_title: Optional[str], participants: Optional[List[str]]) -> Dict:
        return {
            "meeting_title": meeting_title or "Meeting Minutes",
            "summary": f"Meeting transcript processed. Original transcript length: {len(transcript)} characters.",
            "key_points": ["Unable to automatically extract key points", "Please review the original transcript"],
            "action_items": ["Review meeting transcript for action items"],
            "participants": participants or ["Participants not identified"]
        }
