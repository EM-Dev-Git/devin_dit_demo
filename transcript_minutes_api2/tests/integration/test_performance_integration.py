import pytest
import threading
import time

class TestPerformanceIntegration:
    @pytest.mark.slow
    def test_concurrent_user_load(self, integration_client, mock_openai_client):
        """同時ユーザー負荷テスト"""
        results = []
        start_time = time.time()
        
        def user_workflow(user_id):
            try:
                register_data = {
                    "username": f"loaduser{user_id}",
                    "email": f"load{user_id}@test.com",
                    "password": "load123"
                }
                register_response = integration_client.post("/auth/register", json=register_data)
                
                login_data = {"username": f"loaduser{user_id}", "password": "load123"}
                login_response = integration_client.post("/auth/login", json=login_data)
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                transcript_data = {
                    "transcript": f"ユーザー{user_id}の負荷テスト会議内容",
                    "title": f"負荷テスト会議{user_id}"
                }
                minutes_response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
                
                results.append({
                    "user_id": user_id,
                    "success": minutes_response.status_code == 201,
                    "response_time": time.time() - start_time
                })
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "error": str(e)
                })
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=user_workflow, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            avg_response_time = sum(r.get("response_time", 0) for r in successful_results) / len(successful_results)
            assert avg_response_time < 30.0
        
        assert success_rate >= 0.6
    
    @pytest.mark.slow
    def test_large_transcript_processing(self, integration_client, integration_auth_headers, mock_openai_client):
        """大量トランスクリプト処理テスト"""
        large_transcript = "会議内容: " + "テストデータ " * 500
        
        transcript_data = {
            "transcript": large_transcript,
            "title": "大量データテスト会議"
        }
        
        start_time = time.time()
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
        processing_time = time.time() - start_time
        
        assert response.status_code == 201
        assert processing_time < 30.0
        
        minutes_data = response.json()
        assert len(minutes_data["generated_minutes"]) > 0
    
    def test_database_query_performance(self, integration_client, integration_auth_headers, mock_openai_client):
        """データベースクエリパフォーマンステスト"""
        for i in range(10):
            transcript_data = {
                "transcript": f"パフォーマンステスト{i}の内容",
                "title": f"パフォーマンステスト{i}"
            }
            response = integration_client.post("/minutes/generate", json=transcript_data, headers=integration_auth_headers)
            assert response.status_code == 201
        
        start_time = time.time()
        history_response = integration_client.get("/minutes/history", headers=integration_auth_headers)
        query_time = time.time() - start_time
        
        assert history_response.status_code == 200
        assert len(history_response.json()["minutes"]) == 10
        assert query_time < 5.0
