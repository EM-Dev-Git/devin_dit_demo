import pytest
import os

class TestOpenAIDatabaseIntegration:
    def test_minutes_generation_database_persistence_flow(self, integration_client, integration_auth_headers, mock_openai_client):
        """議事録生成からDB保存までの完全フロー"""
        transcript_data = {
            "transcript": "これはテスト用の会議トランスクリプトです。",
            "title": "統合テスト会議"
        }
        
        response = integration_client.post(
            "/minutes/generate", 
            json=transcript_data, 
            headers=integration_auth_headers
        )
        assert response.status_code == 201
        minutes_id = response.json()["id"]
        
        get_response = integration_client.get(
            f"/minutes/{minutes_id}", 
            headers=integration_auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "統合テスト会議"
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    def test_real_openai_api_integration(self, integration_client, integration_auth_headers):
        """実際のOpenAI APIとの統合テスト"""
        transcript_data = {
            "transcript": "会議参加者: 田中、佐藤。議題: プロジェクト計画。田中: スケジュールを確認しましょう。佐藤: 2週間で完了予定です。",
            "title": "実際のAPI統合テスト"
        }
        
        response = integration_client.post(
            "/minutes/generate", 
            json=transcript_data, 
            headers=integration_auth_headers
        )
        assert response.status_code == 201
        
        minutes_data = response.json()
        assert len(minutes_data["generated_minutes"]) > 0
        assert minutes_data["title"] == "実際のAPI統合テスト"
    
    def test_openai_failure_database_rollback(self, integration_client, integration_auth_headers, mocker):
        """OpenAI失敗時のデータベースロールバック"""
        mocker.patch('app.modules.openai_client.client.chat.completions.create', 
                    side_effect=Exception("API Error"))
        
        transcript_data = {"transcript": "テストトランスクリプト", "title": "失敗テスト"}
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
        
        assert response.status_code == 500
        
        history_response = integration_client.get("/minutes/history", headers=integration_auth_headers)
        assert len(history_response.json()["minutes"]) == 0
