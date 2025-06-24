import pytest

class TestGraphAPIWorkflow:
    def test_teams_meeting_complete_workflow(self, integration_client, integration_auth_headers, mock_graph_client, mock_openai_client):
        """Teams会議処理の完全ワークフロー"""
        mock_graph_client.get_user_meetings.return_value = [
            {
                "id": "meeting1",
                "subject": "週次ミーティング",
                "start_time": "2025-06-24T10:00:00Z",
                "end_time": "2025-06-24T11:00:00Z"
            }
        ]
        
        meetings_response = integration_client.get("/graph/meetings/test-user-id", headers=integration_auth_headers)
        assert meetings_response.status_code == 200
        meetings = meetings_response.json()["meetings"]
        assert len(meetings) == 1
        
        mock_graph_client.get_meeting_transcripts.return_value = [
            {
                "id": "transcript1",
                "created_date_time": "2025-06-24T10:00:00Z",
                "end_date_time": "2025-06-24T11:00:00Z"
            }
        ]
        
        transcripts_response = integration_client.get(
            "/graph/meetings/test-user-id/meeting1/transcripts", 
            headers=integration_auth_headers
        )
        assert transcripts_response.status_code == 200
        transcripts = transcripts_response.json()["transcripts"]
        assert len(transcripts) == 1
        
        mock_graph_client.get_transcript_content.return_value = "詳細な会議内容のトランスクリプト"
        
        content_response = integration_client.get(
            "/graph/meetings/test-user-id/meeting1/transcripts/transcript1/content",
            headers=integration_auth_headers
        )
        assert content_response.status_code == 200
        assert "詳細な会議内容" in content_response.json()["content"]
        
        generate_data = {
            "user_id": "test-user-id",
            "meeting_id": "meeting1",
            "transcript_id": "transcript1",
            "title": "週次ミーティング議事録"
        }
        
        minutes_response = integration_client.post(
            "/graph/generate-minutes",
            json=generate_data,
            headers=integration_auth_headers
        )
        assert minutes_response.status_code == 201
        
        minutes_id = minutes_response.json()["id"]
        final_response = integration_client.get(f"/minutes/{minutes_id}", headers=integration_auth_headers)
        assert final_response.status_code == 200
        assert final_response.json()["title"] == "週次ミーティング議事録"
    
    def test_graph_api_error_scenarios(self, integration_client, integration_auth_headers, mock_graph_client):
        """Graph API エラーシナリオテスト"""
        error_scenarios = [
            ("Unauthorized", "認証エラー"),
            ("NotFound", "リソースが見つからない"),
            ("TooManyRequests", "レート制限"),
            ("InternalServerError", "サーバーエラー")
        ]
        
        for error_type, description in error_scenarios:
            mock_graph_client.get_user_meetings.side_effect = Exception(f"Graph API Error: {error_type}")
            
            response = integration_client.get("/graph/meetings/test-user-id", headers=integration_auth_headers)
            assert response.status_code == 500
