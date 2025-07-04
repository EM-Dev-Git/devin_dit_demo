import os
from typing import List, Dict, Optional
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from modules.logger import get_logger

logger = get_logger(__name__)

class GraphClient:
    def __init__(self, validate_credentials=True):
        self.client_id = os.getenv("GRAPH_CLIENT_ID")
        self.client_secret = os.getenv("GRAPH_CLIENT_SECRET")
        self.tenant_id = os.getenv("GRAPH_TENANT_ID")
        self.scopes = [os.getenv("GRAPH_SCOPES", "https://graph.microsoft.com/.default")]
        
        self.credentials_configured = all([self.client_id, self.client_secret, self.tenant_id])
        
        if validate_credentials and not self.credentials_configured:
            raise ValueError("Microsoft Graph credentials not properly configured")
        
        if self.credentials_configured:
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            self.client = GraphServiceClient(
                credentials=self.credential,
                scopes=self.scopes
            )
        else:
            self.credential = None
            self.client = None

    async def get_user_meetings(self, user_id: str, limit: int = 50) -> List[Dict]:
        if not self.credentials_configured:
            raise Exception("Microsoft Graph credentials not configured")
            
        try:
            logger.info(f"Retrieving meetings for user: {user_id}")
            
            meetings = await self.client.users.by_user_id(user_id).online_meetings.get(
                request_configuration=lambda config: setattr(config.query_parameters, 'top', limit)
            )
            
            if not meetings or not meetings.value:
                logger.warning(f"No meetings found for user: {user_id}")
                return []
            
            meeting_list = []
            for meeting in meetings.value:
                meeting_data = {
                    "id": meeting.id,
                    "subject": meeting.subject,
                    "start_time": meeting.start_date_time.isoformat() if meeting.start_date_time else None,
                    "end_time": meeting.end_date_time.isoformat() if meeting.end_date_time else None,
                    "join_url": meeting.join_web_url,
                    "organizer": meeting.participants.organizer.identity.user.display_name if meeting.participants and meeting.participants.organizer else None
                }
                meeting_list.append(meeting_data)
            
            logger.info(f"Retrieved {len(meeting_list)} meetings for user: {user_id}")
            return meeting_list
            
        except ODataError as e:
            logger.error(f"Graph API error retrieving meetings: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to retrieve meetings: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving meetings: {str(e)}")
            raise Exception(f"Failed to retrieve meetings: {str(e)}")

    async def get_meeting_transcripts(self, user_id: str, meeting_id: str) -> List[Dict]:
        if not self.credentials_configured:
            raise Exception("Microsoft Graph credentials not configured")
            
        try:
            logger.info(f"Retrieving transcripts for meeting: {meeting_id}")
            
            transcripts = await self.client.users.by_user_id(user_id).online_meetings.by_online_meeting_id(meeting_id).transcripts.get()
            
            if not transcripts or not transcripts.value:
                logger.warning(f"No transcripts found for meeting: {meeting_id}")
                return []
            
            transcript_list = []
            for transcript in transcripts.value:
                transcript_data = {
                    "id": transcript.id,
                    "created_date_time": transcript.created_date_time.isoformat() if transcript.created_date_time else None,
                    "meeting_id": transcript.meeting_id,
                    "transcript_content_url": transcript.transcript_content_url
                }
                transcript_list.append(transcript_data)
            
            logger.info(f"Retrieved {len(transcript_list)} transcripts for meeting: {meeting_id}")
            return transcript_list
            
        except ODataError as e:
            logger.error(f"Graph API error retrieving transcripts: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to retrieve transcripts: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving transcripts: {str(e)}")
            raise Exception(f"Failed to retrieve transcripts: {str(e)}")

    async def get_transcript_content(self, user_id: str, meeting_id: str, transcript_id: str) -> str:
        if not self.credentials_configured:
            raise Exception("Microsoft Graph credentials not configured")
            
        try:
            logger.info(f"Retrieving transcript content: {transcript_id}")
            
            transcript_content = await self.client.users.by_user_id(user_id).online_meetings.by_online_meeting_id(meeting_id).transcripts.by_call_transcript_id(transcript_id).content.get()
            
            if not transcript_content:
                logger.warning(f"No content found for transcript: {transcript_id}")
                return ""
            
            content = transcript_content.decode('utf-8') if isinstance(transcript_content, bytes) else str(transcript_content)
            
            logger.info(f"Retrieved transcript content for transcript: {transcript_id}")
            return content
            
        except ODataError as e:
            logger.error(f"Graph API error retrieving transcript content: {e.error.message if e.error else str(e)}")
            raise Exception(f"Failed to retrieve transcript content: {e.error.message if e.error else str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving transcript content: {str(e)}")
            raise Exception(f"Failed to retrieve transcript content: {str(e)}")

graph_client = GraphClient(validate_credentials=False)

async def get_user_meetings_list(user_id: str, limit: int = 50) -> List[Dict]:
    return await graph_client.get_user_meetings(user_id, limit)

async def get_meeting_transcripts_list(user_id: str, meeting_id: str) -> List[Dict]:
    return await graph_client.get_meeting_transcripts(user_id, meeting_id)

async def retrieve_transcript_content(user_id: str, meeting_id: str, transcript_id: str) -> str:
    return await graph_client.get_transcript_content(user_id, meeting_id, transcript_id)
