from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from azure.identity import ClientSecretCredential
from typing import List, Optional
import os
from dotenv import load_dotenv
from app.modules.logger import logger

load_dotenv()

TENANT_ID = os.getenv("GRAPH_TENANT_ID")
CLIENT_ID = os.getenv("GRAPH_CLIENT_ID") 
CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET")

class GraphClient:
    def __init__(self):
        if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
            logger.warning("Graph API credentials not fully configured")
            self.client = None
            return
            
        try:
            credential = ClientSecretCredential(
                tenant_id=TENANT_ID,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET
            )
            
            self.client = GraphServiceClient(
                credentials=credential,
                scopes=['https://graph.microsoft.com/.default']
            )
            logger.info("Graph client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graph client: {str(e)}")
            self.client = None
    
    async def get_user_meetings(self, user_id: str) -> List[dict]:
        if not self.client:
            raise ValueError("Graph client not initialized")
            
        try:
            logger.info(f"Fetching meetings for user: {user_id}")
            
            meetings = await self.client.users.by_user_id(user_id).online_meetings.get()
            
            if not meetings or not meetings.value:
                return []
                
            return [
                {
                    "id": meeting.id,
                    "subject": meeting.subject,
                    "start_time": meeting.start_date_time.isoformat() if meeting.start_date_time else None,
                    "end_time": meeting.end_date_time.isoformat() if meeting.end_date_time else None,
                    "join_url": meeting.join_web_url
                }
                for meeting in meetings.value
            ]
            
        except ODataError as e:
            logger.error(f"Graph API error fetching meetings: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to fetch meetings: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error fetching meetings: {str(e)}")
            raise Exception(f"Failed to fetch meetings: {str(e)}")
    
    async def get_meeting_transcripts(self, user_id: str, meeting_id: str) -> List[dict]:
        if not self.client:
            raise ValueError("Graph client not initialized")
            
        try:
            logger.info(f"Fetching transcripts for meeting: {meeting_id}")
            
            transcripts = await self.client.users.by_user_id(user_id).online_meetings.by_online_meeting_id(meeting_id).transcripts.get()
            
            if not transcripts or not transcripts.value:
                return []
                
            return [
                {
                    "id": transcript.id,
                    "created_date_time": transcript.created_date_time.isoformat() if transcript.created_date_time else None,
                    "end_date_time": transcript.end_date_time.isoformat() if transcript.end_date_time else None,
                    "content_url": transcript.transcript_content_url
                }
                for transcript in transcripts.value
            ]
            
        except ODataError as e:
            logger.error(f"Graph API error fetching transcripts: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to fetch transcripts: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error fetching transcripts: {str(e)}")
            raise Exception(f"Failed to fetch transcripts: {str(e)}")
    
    async def get_transcript_content(self, user_id: str, meeting_id: str, transcript_id: str) -> str:
        if not self.client:
            raise ValueError("Graph client not initialized")
            
        try:
            logger.info(f"Fetching transcript content: {transcript_id}")
            
            content = await self.client.users.by_user_id(user_id).online_meetings.by_online_meeting_id(meeting_id).transcripts.by_call_transcript_id(transcript_id).content.get()
            
            if content:
                return content.decode('utf-8') if isinstance(content, bytes) else str(content)
            else:
                return ""
                
        except ODataError as e:
            logger.error(f"Graph API error fetching transcript content: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to fetch transcript content: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error fetching transcript content: {str(e)}")
            raise Exception(f"Failed to fetch transcript content: {str(e)}")

graph_client = GraphClient()
