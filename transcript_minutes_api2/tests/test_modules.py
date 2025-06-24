import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
from app.modules.auth_handler import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, authenticate_user
)
from app.modules.openai_client import generate_minutes
from app.modules.graph_client import GraphClient
from app.modules.database import User, Minutes
from app.schemas.auth import TokenData
from fastapi import HTTPException

class TestAuthHandler:
    def test_verify_password_success(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_get_password_hash(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password

    def test_create_access_token_default_expiry(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_custom_expiry(self):
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        credentials_exception = HTTPException(status_code=401, detail="Test exception")
        
        token_data = verify_token(token, credentials_exception)
        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"

    def test_verify_token_invalid(self):
        invalid_token = "invalid.token.here"
        credentials_exception = HTTPException(status_code=401, detail="Test exception")
        
        with pytest.raises(HTTPException):
            verify_token(invalid_token, credentials_exception)

    def test_authenticate_user_success(self, db_session, test_user):
        user = authenticate_user(db_session, test_user.username, "testpassword123")
        assert user is not False
        assert user.username == test_user.username

    def test_authenticate_user_wrong_password(self, db_session, test_user):
        user = authenticate_user(db_session, test_user.username, "wrongpassword")
        assert user is False

    def test_authenticate_user_nonexistent(self, db_session):
        user = authenticate_user(db_session, "nonexistent", "password")
        assert user is False

class TestOpenAIClient:
    @pytest.mark.asyncio
    async def test_generate_minutes_success(self, mocker):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "生成された議事録"
        mock_response.usage.total_tokens = 100
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('app.modules.openai_client.client', mock_client)
        mocker.patch('app.modules.openai_client.OPENAI_API_KEY', 'test-key')
        
        result = await generate_minutes("テストトランスクリプト", user_id=1)
        assert result == "生成された議事録"

    @pytest.mark.asyncio
    async def test_generate_minutes_with_title(self, mocker):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "タイトル付き議事録"
        mock_response.usage.total_tokens = 120
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('app.modules.openai_client.client', mock_client)
        mocker.patch('app.modules.openai_client.OPENAI_API_KEY', 'test-key')
        
        result = await generate_minutes("テストトランスクリプト", user_id=1, title="テスト会議")
        assert result == "タイトル付き議事録"

    @pytest.mark.asyncio
    async def test_generate_minutes_no_api_key(self, mocker):
        mocker.patch('app.modules.openai_client.OPENAI_API_KEY', None)
        
        with pytest.raises(Exception) as exc_info:
            await generate_minutes("テストトランスクリプト", user_id=1)
        assert "OpenAI API key not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_minutes_api_error(self, mocker):
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        mocker.patch('app.modules.openai_client.client', mock_client)
        mocker.patch('app.modules.openai_client.OPENAI_API_KEY', 'test-key')
        
        with pytest.raises(Exception) as exc_info:
            await generate_minutes("テストトランスクリプト", user_id=1)
        assert "議事録の生成に失敗しました" in str(exc_info.value)

class TestGraphClient:
    def test_graph_client_init_success(self, mocker):
        mocker.patch('app.modules.graph_client.TENANT_ID', 'test-tenant')
        mocker.patch('app.modules.graph_client.CLIENT_ID', 'test-client')
        mocker.patch('app.modules.graph_client.CLIENT_SECRET', 'test-secret')
        
        mock_credential = mocker.patch('app.modules.graph_client.ClientSecretCredential')
        mock_graph_client = mocker.patch('app.modules.graph_client.GraphServiceClient')
        
        client = GraphClient()
        assert client.client is not None
        mock_credential.assert_called_once()
        mock_graph_client.assert_called_once()

    def test_graph_client_init_missing_credentials(self, mocker):
        mocker.patch('app.modules.graph_client.TENANT_ID', None)
        mocker.patch('app.modules.graph_client.CLIENT_ID', 'test-client')
        mocker.patch('app.modules.graph_client.CLIENT_SECRET', 'test-secret')
        
        client = GraphClient()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_get_user_meetings_success(self, mocker):
        mock_meeting = MagicMock()
        mock_meeting.id = "meeting1"
        mock_meeting.subject = "テスト会議"
        mock_meeting.start_date_time = None
        mock_meeting.end_date_time = None
        mock_meeting.join_web_url = "https://teams.microsoft.com/join"
        
        mock_meetings = MagicMock()
        mock_meetings.value = [mock_meeting]
        
        mock_client = MagicMock()
        mock_user_request = MagicMock()
        mock_user_request.online_meetings = MagicMock()
        mock_user_request.online_meetings.get = AsyncMock(return_value=mock_meetings)
        mock_client.users.by_user_id.return_value = mock_user_request
        
        graph_client = GraphClient()
        graph_client.client = mock_client
        
        result = await graph_client.get_user_meetings("test_user")
        assert len(result) == 1
        assert result[0]["id"] == "meeting1"
        assert result[0]["subject"] == "テスト会議"

    @pytest.mark.asyncio
    async def test_get_user_meetings_client_not_initialized(self):
        graph_client = GraphClient()
        graph_client.client = None
        
        with pytest.raises(ValueError) as exc_info:
            await graph_client.get_user_meetings("test_user")
        assert "Graph client not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_meeting_transcripts_success(self, mocker):
        mock_transcript = MagicMock()
        mock_transcript.id = "transcript1"
        mock_transcript.created_date_time = None
        mock_transcript.end_date_time = None
        mock_transcript.transcript_content_url = "https://example.com/transcript"
        
        mock_transcripts = MagicMock()
        mock_transcripts.value = [mock_transcript]
        
        mock_client = MagicMock()
        mock_user_request = MagicMock()
        mock_meeting_request = MagicMock()
        mock_meeting_request.transcripts = MagicMock()
        mock_meeting_request.transcripts.get = AsyncMock(return_value=mock_transcripts)
        mock_user_request.online_meetings.by_online_meeting_id.return_value = mock_meeting_request
        mock_client.users.by_user_id.return_value = mock_user_request
        
        graph_client = GraphClient()
        graph_client.client = mock_client
        
        result = await graph_client.get_meeting_transcripts("test_user", "meeting1")
        assert len(result) == 1
        assert result[0]["id"] == "transcript1"

    @pytest.mark.asyncio
    async def test_get_transcript_content_success(self, mocker):
        mock_content = "テスト用トランスクリプト内容"
        
        mock_client = MagicMock()
        mock_user_request = MagicMock()
        mock_meeting_request = MagicMock()
        mock_transcript_request = MagicMock()
        mock_transcript_request.content = MagicMock()
        mock_transcript_request.content.get = AsyncMock(return_value=mock_content)
        mock_meeting_request.transcripts.by_call_transcript_id.return_value = mock_transcript_request
        mock_user_request.online_meetings.by_online_meeting_id.return_value = mock_meeting_request
        mock_client.users.by_user_id.return_value = mock_user_request
        
        graph_client = GraphClient()
        graph_client.client = mock_client
        
        result = await graph_client.get_transcript_content("test_user", "meeting1", "transcript1")
        assert result == mock_content

    @pytest.mark.asyncio
    async def test_get_transcript_content_client_not_initialized(self):
        graph_client = GraphClient()
        graph_client.client = None
        
        with pytest.raises(ValueError) as exc_info:
            await graph_client.get_transcript_content("test_user", "meeting1", "transcript1")
        assert "Graph client not initialized" in str(exc_info.value)

class TestDatabaseModels:
    def test_user_creation(self, db_session):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_minutes_creation(self, db_session, test_user):
        minutes = Minutes(
            user_id=test_user.id,
            title="テスト会議",
            transcript="テストトランスクリプト",
            generated_minutes="テスト議事録"
        )
        db_session.add(minutes)
        db_session.commit()
        
        assert minutes.id is not None
        assert minutes.user_id == test_user.id
        assert minutes.title == "テスト会議"
        assert minutes.created_at is not None

    def test_user_minutes_relationship(self, db_session, test_user):
        minutes1 = Minutes(
            user_id=test_user.id,
            title="会議1",
            transcript="内容1",
            generated_minutes="議事録1"
        )
        minutes2 = Minutes(
            user_id=test_user.id,
            title="会議2",
            transcript="内容2",
            generated_minutes="議事録2"
        )
        db_session.add_all([minutes1, minutes2])
        db_session.commit()
        
        db_session.refresh(test_user)
        assert len(test_user.minutes) == 2
        assert minutes1.user == test_user
        assert minutes2.user == test_user

    def test_cascade_delete(self, db_session, test_user):
        minutes = Minutes(
            user_id=test_user.id,
            title="削除テスト",
            transcript="削除テスト内容",
            generated_minutes="削除テスト議事録"
        )
        db_session.add(minutes)
        db_session.commit()
        minutes_id = minutes.id
        
        db_session.delete(test_user)
        db_session.commit()
        
        deleted_minutes = db_session.query(Minutes).filter(Minutes.id == minutes_id).first()
        assert deleted_minutes is None
