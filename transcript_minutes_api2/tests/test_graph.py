import pytest
from fastapi import status
from unittest.mock import AsyncMock

class TestGraphMeetings:
    def test_get_user_meetings_success(self, client, auth_headers, mock_graph_client):
        response = client.get("/graph/meetings/test_user_id", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "meeting1"
        assert data[0]["subject"] == "テスト会議1"

    def test_get_user_meetings_graph_not_configured(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_user_meetings', side_effect=ValueError("Graph client not initialized"))
        
        response = client.get("/graph/meetings/test_user_id", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Graph client not initialized" in response.json()["detail"]

    def test_get_user_meetings_api_error(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_user_meetings', side_effect=Exception("Graph API Error"))
        
        response = client.get("/graph/meetings/test_user_id", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Graph API Error" in response.json()["detail"]

    def test_get_user_meetings_unauthorized(self, client):
        response = client.get("/graph/meetings/test_user_id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_meetings_empty_result(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_user_meetings', return_value=[])
        
        response = client.get("/graph/meetings/test_user_id", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

class TestGraphTranscripts:
    def test_get_meeting_transcripts_success(self, client, auth_headers, mock_graph_client):
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "transcript1"

    def test_get_meeting_transcripts_graph_not_configured(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_meeting_transcripts', side_effect=ValueError("Graph client not initialized"))
        
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_meeting_transcripts_api_error(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_meeting_transcripts', side_effect=Exception("Graph API Error"))
        
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_meeting_transcripts_unauthorized(self, client):
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestGraphTranscriptContent:
    def test_get_transcript_content_success(self, client, auth_headers, mock_graph_client):
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts/transcript1/content", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "テスト用トランスクリプト内容"

    def test_get_transcript_content_not_found(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_transcript_content', return_value="")
        
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts/nonexistent/content", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == ""

    def test_get_transcript_content_graph_not_configured(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_transcript_content', side_effect=ValueError("Graph client not initialized"))
        
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts/transcript1/content", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_transcript_content_unauthorized(self, client):
        response = client.get("/graph/meetings/test_user_id/meeting1/transcripts/transcript1/content")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestGraphMinutesGenerate:
    def test_generate_minutes_from_graph_success(self, client, auth_headers, mock_graph_client, mocker, mock_openai_response):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', return_value=mock_openai_response)
        
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "Graph会議議事録"
        }
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Graph会議議事録"
        assert data["transcript"] == "テスト用トランスクリプト内容"
        assert data["generated_minutes"] == "生成された議事録内容"

    def test_generate_minutes_from_graph_without_title(self, client, auth_headers, mock_graph_client, mocker, mock_openai_response):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', return_value=mock_openai_response)
        
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1"
        }
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] is None

    def test_generate_minutes_from_graph_transcript_not_found(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_transcript_content', return_value="")
        
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "nonexistent",
            "title": "存在しないトランスクリプト"
        }
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Transcript content not found" in response.json()["detail"]

    def test_generate_minutes_from_graph_graph_error(self, client, auth_headers, mocker):
        mocker.patch('app.modules.graph_client.graph_client.get_transcript_content', side_effect=Exception("Graph API Error"))
        
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "エラーテスト"
        }
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_generate_minutes_from_graph_openai_error(self, client, auth_headers, mock_graph_client, mocker):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', side_effect=Exception("OpenAI API Error"))
        
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "OpenAIエラーテスト"
        }
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_generate_minutes_from_graph_unauthorized(self, client):
        request_data = {
            "user_id": "test_user_id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "認証テスト"
        }
        response = client.post("/graph/minutes/generate", json=request_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_generate_minutes_from_graph_missing_fields(self, client, auth_headers):
        request_data = {"user_id": "test_user_id"}
        response = client.post("/graph/minutes/generate", json=request_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
