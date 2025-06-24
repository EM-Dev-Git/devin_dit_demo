import pytest
import os

class TestGraphSDKIntegration:
    @pytest.mark.skipif(
        not all([os.getenv("GRAPH_TENANT_ID"), os.getenv("GRAPH_CLIENT_ID"), os.getenv("GRAPH_CLIENT_SECRET")]),
        reason="Graph API credentials not configured"
    )
    def test_graph_sdk_initialization(self, integration_client):
        """Graph SDK初期化テスト"""
        from app.modules.graph_client import graph_client
        
        assert graph_client.client is not None
    
    def test_graph_api_error_handling(self, integration_client, integration_auth_headers, mock_graph_client):
        """Graph API エラーハンドリング統合テスト"""
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
            assert error_type in response.json()["detail"]
    
    def test_graph_api_mock_responses(self, integration_client, integration_auth_headers, mock_graph_client):
        """Graph API モックレスポンステスト"""
        mock_graph_client.get_user_meetings.return_value = [
            {"id": "meeting1", "subject": "テスト会議", "start_time": "2025-06-24T10:00:00Z"}
        ]
        
        response = integration_client.get("/graph/meetings/test-user-id", headers=integration_auth_headers)
        assert response.status_code == 200
        meetings = response.json()["meetings"]
        assert len(meetings) == 1
        assert meetings[0]["subject"] == "テスト会議"
        
        mock_graph_client.get_meeting_transcripts.return_value = [
            {"id": "transcript1", "created_date_time": "2025-06-24T10:00:00Z"}
        ]
        
        transcripts_response = integration_client.get(
            "/graph/meetings/test-user-id/meeting1/transcripts",
            headers=integration_auth_headers
        )
        assert transcripts_response.status_code == 200
        transcripts = transcripts_response.json()["transcripts"]
        assert len(transcripts) == 1
