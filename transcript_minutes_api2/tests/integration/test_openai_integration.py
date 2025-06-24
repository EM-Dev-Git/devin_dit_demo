import pytest
import os
import time

class TestOpenAPIIntegration:
    @pytest.mark.slow
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not configured")
    def test_real_openai_api_call(self, integration_client, integration_auth_headers):
        """実際のOpenAI APIとの統合テスト"""
        transcript_data = {
            "transcript": """
            会議参加者: 田中、佐藤、鈴木
            議題: 来月のプロジェクト計画について
            田中: 来月のスケジュールを確認しましょう。
            佐藤: 開発フェーズは2週間を予定しています。
            鈴木: テストフェーズも含めて3週間必要です。
            田中: 了解しました。リソース配分を検討します。
            """,
            "title": "プロジェクト計画会議"
        }
        
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
        assert response.status_code == 201
        
        minutes_data = response.json()
        assert "田中" in minutes_data["generated_minutes"]
        assert "プロジェクト" in minutes_data["generated_minutes"]
        assert minutes_data["title"] == "プロジェクト計画会議"
    
    @pytest.mark.slow
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not configured")
    def test_openai_rate_limiting(self, integration_client, integration_auth_headers):
        """OpenAI APIレート制限テスト"""
        responses = []
        for i in range(3):
            transcript_data = {
                "transcript": f"レート制限テスト{i}の内容",
                "title": f"テスト会議{i}"
            }
            response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
            responses.append(response)
            time.sleep(2)
        
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 2
    
    def test_openai_error_handling(self, integration_client, integration_auth_headers, mocker):
        """OpenAI APIエラーハンドリングテスト"""
        mocker.patch('app.modules.openai_client.client.chat.completions.create', 
                    side_effect=Exception("OpenAI API Error"))
        
        transcript_data = {"transcript": "エラーテスト", "title": "エラー会議"}
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
