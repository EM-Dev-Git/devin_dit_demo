import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.auth import UserCreate, UserLogin, Token, TokenData, UserResponse
from app.schemas.minutes import MinutesGenerate, MinutesResponse, MinutesHistoryResponse
from app.schemas.users import UserProfileResponse, UserUpdate
from app.schemas.graph import (
    MeetingInfo, MeetingListResponse, TranscriptInfo, 
    TranscriptListResponse, TranscriptContentResponse, GraphMinutesGenerate
)

class TestAuthSchemas:
    def test_user_create_valid(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "securepassword123"

    def test_user_create_invalid_username_too_short(self):
        user_data = {
            "username": "ab",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_invalid_username_special_chars(self):
        user_data = {
            "username": "user@name",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_invalid_email(self):
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "securepassword123"
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_invalid_password_too_short(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short"
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_login_valid(self):
        login_data = {
            "username": "testuser",
            "password": "securepassword123"
        }
        login = UserLogin(**login_data)
        assert login.username == "testuser"
        assert login.password == "securepassword123"

    def test_user_login_missing_fields(self):
        with pytest.raises(ValidationError):
            UserLogin(username="testuser")
        
        with pytest.raises(ValidationError):
            UserLogin(password="password")

    def test_token_valid(self):
        token_data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            "token_type": "bearer"
        }
        token = Token(**token_data)
        assert token.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        assert token.token_type == "bearer"

    def test_token_data_valid(self):
        token_data = TokenData(username="testuser")
        assert token_data.username == "testuser"

    def test_token_data_optional(self):
        token_data = TokenData()
        assert token_data.username is None

    def test_user_response_valid(self):
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": datetime.now()
        }
        user = UserResponse(**user_data)
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None

class TestMinutesSchemas:
    def test_minutes_generate_valid(self):
        minutes_data = {
            "transcript": "これは有効なトランスクリプトです。",
            "title": "テスト会議"
        }
        minutes = MinutesGenerate(**minutes_data)
        assert minutes.transcript == "これは有効なトランスクリプトです。"
        assert minutes.title == "テスト会議"

    def test_minutes_generate_without_title(self):
        minutes_data = {
            "transcript": "これはタイトルなしのトランスクリプトです。"
        }
        minutes = MinutesGenerate(**minutes_data)
        assert minutes.transcript == "これはタイトルなしのトランスクリプトです。"
        assert minutes.title is None

    def test_minutes_generate_transcript_too_short(self):
        minutes_data = {
            "transcript": "短い",
            "title": "テスト会議"
        }
        with pytest.raises(ValidationError):
            MinutesGenerate(**minutes_data)

    def test_minutes_generate_transcript_too_long(self):
        minutes_data = {
            "transcript": "a" * 10001,
            "title": "テスト会議"
        }
        with pytest.raises(ValidationError):
            MinutesGenerate(**minutes_data)

    def test_minutes_generate_title_too_long(self):
        minutes_data = {
            "transcript": "これは有効なトランスクリプトです。",
            "title": "a" * 201
        }
        with pytest.raises(ValidationError):
            MinutesGenerate(**minutes_data)

    def test_minutes_response_valid(self):
        minutes_data = {
            "id": 1,
            "user_id": 1,
            "title": "テスト会議",
            "transcript": "テストトランスクリプト",
            "generated_minutes": "テスト議事録",
            "created_at": datetime.now()
        }
        minutes = MinutesResponse(**minutes_data)
        assert minutes.id == 1
        assert minutes.user_id == 1
        assert minutes.title == "テスト会議"

    def test_minutes_history_response_valid(self):
        history_data = {
            "id": 1,
            "title": "テスト会議",
            "created_at": datetime.now()
        }
        history = MinutesHistoryResponse(**history_data)
        assert history.id == 1
        assert history.title == "テスト会議"
        assert history.created_at is not None

class TestUsersSchemas:
    def test_user_profile_response_valid(self):
        profile_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        profile = UserProfileResponse(**profile_data)
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"

    def test_user_update_valid_username(self):
        update_data = {"username": "newusername"}
        update = UserUpdate(**update_data)
        assert update.username == "newusername"
        assert update.email is None

    def test_user_update_valid_email(self):
        update_data = {"email": "new@example.com"}
        update = UserUpdate(**update_data)
        assert update.username is None
        assert update.email == "new@example.com"

    def test_user_update_both_fields(self):
        update_data = {
            "username": "newusername",
            "email": "new@example.com"
        }
        update = UserUpdate(**update_data)
        assert update.username == "newusername"
        assert update.email == "new@example.com"

    def test_user_update_empty(self):
        update = UserUpdate()
        assert update.username is None
        assert update.email is None

    def test_user_update_invalid_username_too_short(self):
        update_data = {"username": "ab"}
        with pytest.raises(ValidationError):
            UserUpdate(**update_data)

    def test_user_update_invalid_username_special_chars(self):
        update_data = {"username": "user@name"}
        with pytest.raises(ValidationError):
            UserUpdate(**update_data)

    def test_user_update_invalid_email(self):
        update_data = {"email": "invalid-email"}
        with pytest.raises(ValidationError):
            UserUpdate(**update_data)

class TestGraphSchemas:
    def test_meeting_info_valid(self):
        meeting_data = {
            "id": "meeting1",
            "subject": "テスト会議",
            "start_time": "2025-06-24T10:00:00Z",
            "end_time": "2025-06-24T11:00:00Z",
            "join_url": "https://teams.microsoft.com/join"
        }
        meeting = MeetingInfo(**meeting_data)
        assert meeting.id == "meeting1"
        assert meeting.subject == "テスト会議"
        assert meeting.start_time == "2025-06-24T10:00:00Z"

    def test_meeting_info_optional_fields(self):
        meeting_data = {
            "id": "meeting1",
            "subject": "テスト会議"
        }
        meeting = MeetingInfo(**meeting_data)
        assert meeting.id == "meeting1"
        assert meeting.subject == "テスト会議"
        assert meeting.start_time is None
        assert meeting.end_time is None
        assert meeting.join_url is None

    def test_meeting_list_response_valid(self):
        meetings_data = [
            {
                "id": "meeting1",
                "subject": "テスト会議1"
            },
            {
                "id": "meeting2",
                "subject": "テスト会議2"
            }
        ]
        meetings = MeetingListResponse(meetings=meetings_data)
        assert len(meetings.meetings) == 2
        assert meetings.meetings[0].id == "meeting1"

    def test_transcript_info_valid(self):
        transcript_data = {
            "id": "transcript1",
            "created_date_time": "2025-06-24T10:00:00Z",
            "end_date_time": "2025-06-24T11:00:00Z",
            "content_url": "https://example.com/transcript"
        }
        transcript = TranscriptInfo(**transcript_data)
        assert transcript.id == "transcript1"
        assert transcript.created_date_time == "2025-06-24T10:00:00Z"

    def test_transcript_info_optional_fields(self):
        transcript_data = {"id": "transcript1"}
        transcript = TranscriptInfo(**transcript_data)
        assert transcript.id == "transcript1"
        assert transcript.created_date_time is None
        assert transcript.end_date_time is None
        assert transcript.content_url is None

    def test_transcript_list_response_valid(self):
        transcripts_data = [
            {"id": "transcript1"},
            {"id": "transcript2"}
        ]
        transcripts = TranscriptListResponse(transcripts=transcripts_data)
        assert len(transcripts.transcripts) == 2
        assert transcripts.transcripts[0].id == "transcript1"

    def test_transcript_content_response_valid(self):
        content_data = {
            "transcript_id": "transcript1",
            "content": "テスト用トランスクリプト内容"
        }
        content = TranscriptContentResponse(**content_data)
        assert content.transcript_id == "transcript1"
        assert content.content == "テスト用トランスクリプト内容"

    def test_graph_minutes_generate_valid(self):
        generate_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "Graph会議議事録"
        }
        generate = GraphMinutesGenerate(**generate_data)
        assert generate.user_id == "test_user_id"
        assert generate.meeting_id == "meeting1"
        assert generate.transcript_id == "transcript1"
        assert generate.title == "Graph会議議事録"

    def test_graph_minutes_generate_without_title(self):
        generate_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1"
        }
        generate = GraphMinutesGenerate(**generate_data)
        assert generate.user_id == "test_user_id"
        assert generate.title is None

    def test_graph_minutes_generate_missing_required_fields(self):
        with pytest.raises(ValidationError):
            GraphMinutesGenerate(user_id="test_user_id")
        
        with pytest.raises(ValidationError):
            GraphMinutesGenerate(meeting_id="meeting1")
        
        with pytest.raises(ValidationError):
            GraphMinutesGenerate(transcript_id="transcript1")
