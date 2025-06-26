import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session

try:
    from msgraph import GraphServiceClient
    from msgraph.generated.models.o_data_errors.o_data_error import ODataError
    from azure.identity import AuthorizationCodeCredential, ClientSecretCredential
except ImportError:
    GraphServiceClient = None
    ODataError = None
    AuthorizationCodeCredential = None
    ClientSecretCredential = None

from modules.database import User
from modules.logger import get_logger

logger = get_logger(__name__)

class GraphClient:
    def __init__(self):
        self.client_id = os.getenv("GRAPH_CLIENT_ID")
        self.client_secret = os.getenv("GRAPH_CLIENT_SECRET")
        self.tenant_id = os.getenv("GRAPH_TENANT_ID")
        self.redirect_uri = os.getenv("GRAPH_REDIRECT_URI")
        
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            raise ValueError("Microsoft Graph configuration is incomplete. Please check environment variables.")
        
        self.scopes = ["https://graph.microsoft.com/OnlineMeetingTranscript.Read.All"]
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
    
    def get_authorization_url(self, state: str = None) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_mode": "query"
        }
        if state:
            params["state"] = state
        
        auth_url = f"{self.authority}/oauth2/v2.0/authorize?" + urlencode(params)
        logger.info(f"Generated Graph authorization URL")
        return auth_url
    
    def exchange_code_for_tokens(self, code: str) -> Dict:
        token_url = f"{self.authority}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(self.scopes)
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully exchanged authorization code for tokens")
            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data["expires_in"],
                "expires_at": datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            }
        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for tokens: {str(e)}")
            raise Exception(f"Token exchange failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        token_url = f"{self.authority}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(self.scopes)
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully refreshed access token")
            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data["expires_in"],
                "expires_at": datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            }
        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def get_valid_token(self, user: User, db: Session) -> str:
        if not user.graph_access_token:
            raise Exception("User has not authorized Microsoft Graph access")
        
        if user.graph_token_expires_at and user.graph_token_expires_at <= datetime.utcnow():
            if not user.graph_refresh_token:
                raise Exception("Access token expired and no refresh token available")
            
            try:
                token_data = self.refresh_access_token(user.graph_refresh_token)
                user.graph_access_token = token_data["access_token"]
                if token_data.get("refresh_token"):
                    user.graph_refresh_token = token_data["refresh_token"]
                user.graph_token_expires_at = token_data["expires_at"]
                db.commit()
                logger.info(f"Refreshed token for user {user.id}")
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user.id}: {str(e)}")
                raise Exception("Failed to refresh access token. Please re-authorize.")
        
        return user.graph_access_token
    
    def get_graph_client(self, access_token: str):
        if not GraphServiceClient:
            raise Exception("Microsoft Graph SDK not available. Please install msgraph-sdk and azure-identity packages.")
        
        credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        client = GraphServiceClient(credentials=credential, scopes=self.scopes)
        return client
    
    def list_meeting_transcripts(self, user: User, db: Session, meeting_id: str) -> List[Dict]:
        try:
            access_token = self.get_valid_token(user, db)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            transcript_list = []
            
            if "value" in data:
                for transcript in data["value"]:
                    transcript_list.append({
                        "id": transcript.get("id"),
                        "created_date_time": transcript.get("createdDateTime"),
                        "meeting_id": transcript.get("meetingId"),
                        "transcript_content_url": transcript.get("transcriptContentUrl")
                    })
            
            logger.info(f"Retrieved {len(transcript_list)} transcripts for meeting {meeting_id}")
            return transcript_list
            
        except requests.RequestException as e:
            logger.error(f"Graph API error retrieving transcripts: {str(e)}")
            raise Exception(f"Failed to retrieve transcripts: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving transcripts: {str(e)}")
            raise Exception(f"Failed to retrieve transcripts: {str(e)}")
    
    def get_transcript_content(self, user: User, db: Session, meeting_id: str, transcript_id: str) -> str:
        try:
            access_token = self.get_valid_token(user, db)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            content = response.text
            logger.info(f"Retrieved transcript content for transcript {transcript_id}")
            return content
                
        except requests.RequestException as e:
            logger.error(f"Graph API error retrieving transcript content: {str(e)}")
            raise Exception(f"Failed to retrieve transcript content: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving transcript content: {str(e)}")
            raise Exception(f"Failed to retrieve transcript content: {str(e)}")
