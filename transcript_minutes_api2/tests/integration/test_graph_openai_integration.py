import pytest
import os

class TestGraphOpenAIIntegration:
    def test_teams_transcript_to_minutes_complete_flow(self, integration_client, integration_auth_headers, mock_graph_client, mock_openai_client):
        """Teams → Graph API → OpenAI → DB の完全フロー"""
        mock_graph_client.get_transcript_content.return_value = "会議の内容です。"
        
        graph_data = {
            "user_id": "test-user-id",
            "meeting_id": "test-meeting-id", 
            "transcript_id": "test-transcript-id",
            "title": "Teams会議"
        }
        
        response = integration_client.post(
            "/graph/generate-minutes", 
            json=graph_data, 
            headers=integration_auth_headers
        )
        assert response.status_code == 201
        
        minutes_data = response.json()
        assert minutes_data["title"] == "Teams会議"
        assert len(minutes_data["generated_minutes"]) > 0
        
        mock_graph_client.get_transcript_content.assert_called_once()
        mock_openai_client.assert_called_once()
    
    def test_graph_api_failure_handling(self, integration_client, integration_auth_headers, mock_graph_client):
        """Graph API失敗時のエラーハンドリング"""
        mock_graph_client.get_transcript_content.side_effect = Exception("Graph API Error")
        
        graph_data = {
            "user_id": "test-user-id",
            "meeting_id": "test-meeting-id",
            "transcript_id": "test-transcript-id",
            "title": "失敗テスト"
        }
        
        response = integration_client.post(
            "/graph/generate-minutes",
            json=graph_data,
            headers=integration_auth_headers
        )
        assert response.status_code == 500
    
    def test_multiple_api_integration_workflow(self, integration_client, integration_auth_headers, mock_graph_client, mock_openai_client):
        """複数API統合ワークフロー"""
        mock_graph_client.get_user_meetings.return_value = [
            {"id": "meeting1", "subject": "週次ミーティング", "start_time": "2025-06-24T10:00:00Z"}
        ]
        
        meetings_response = integration_client.get("/graph/meetings/test-user-id", headers=integration_auth_headers)
        assert meetings_response.status_code == 200
        meetings = meetings_response.json()["meetings"]
        assert len(meetings) == 1
        
        mock_graph_client.get_meeting_transcripts.return_value = [
            {"id": "transcript1", "created_date_time": "2025-06-24T10:00:00Z"}
        ]
        
        transcripts_response = integration_client.get(
            "/graph/meetings/test-user-id/meeting1/transcripts", 
            headers=integration_auth_headers
        )
        assert transcripts_response.status_code == 200
        
        mock_graph_client.get_transcript_content.return_value = "詳細な会議内容"
        
        content_response = integration_client.get(
            "/graph/meetings/test-user-id/meeting1/transcripts/transcript1/content",
            headers=integration_auth_headers
        )
        assert content_response.status_code == 200
        assert "詳細な会議内容" in content_response.json()["content"]
