import pytest
import threading
import time

class TestDatabaseTransactionIntegration:
    def test_user_minutes_transaction_consistency(self, integration_client, mock_openai_client):
        """ユーザーと議事録のトランザクション整合性"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        username = f"txuser_{unique_id}"
        email = f"tx_{unique_id}@test.com"
        
        register_data = {"username": username, "email": email, "password": "tx123"}
        register_response = integration_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"username": username, "password": "tx123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        transcript_data = {"transcript": "トランザクションテスト", "title": "TX会議"}
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
        assert response.status_code == 201
        
        history_response = integration_client.get("/minutes/history", headers=headers)
        assert len(history_response.json()) == 1
    
    def test_concurrent_minutes_generation(self, integration_client, mock_openai_client):
        """同時議事録生成のトランザクション制御"""
        results = []
        
        def generate_minutes(thread_id):
            try:
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                username = f"concurrent{thread_id}_{unique_id}"
                email = f"concurrent{thread_id}_{unique_id}@test.com"
                
                register_data = {
                    "username": username,
                    "email": email,
                    "password": "concurrent123"
                }
                integration_client.post("/auth/register", json=register_data)
                
                login_data = {"username": username, "password": "concurrent123"}
                login_response = integration_client.post("/auth/login", json=login_data)
                headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
                
                transcript_data = {
                    "transcript": f"スレッド{thread_id}のトランスクリプト",
                    "title": f"スレッド{thread_id}会議"
                }
                response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
                results.append((thread_id, response.status_code))
            except Exception as e:
                results.append((thread_id, f"Error: {str(e)}"))
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_minutes, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        success_count = sum(1 for _, status in results if status == 201)
        assert success_count >= 2
    
    def test_transaction_rollback_on_error(self, integration_client, mocker):
        """エラー時のトランザクションロールバック"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        username = f"rollbackuser_{unique_id}"
        email = f"rollback_{unique_id}@test.com"
        
        register_data = {"username": username, "email": email, "password": "rollback123"}
        register_response = integration_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"username": username, "password": "rollback123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        mocker.patch('app.modules.openai_client.client.chat.completions.create', 
                    side_effect=Exception("OpenAI API Error"))
        
        transcript_data = {"transcript": "ロールバックテスト", "title": "ロールバック会議"}
        response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
        assert response.status_code == 500
        
        history_response = integration_client.get("/minutes/history", headers=headers)
        assert len(history_response.json()) == 0
