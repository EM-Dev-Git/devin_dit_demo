import pytest

class TestSecurityIntegration:
    def test_jwt_token_lifecycle_integration(self, integration_client):
        """JWT トークンライフサイクル統合テスト"""
        register_data = {"username": "secuser", "email": "sec@test.com", "password": "sec123"}
        integration_client.post("/auth/register", json=register_data)
        
        login_data = {"username": "secuser", "password": "sec123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = integration_client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        refresh_response = integration_client.post("/auth/refresh", headers=headers)
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        
        new_headers = {"Authorization": f"Bearer {new_token}"}
        profile_response2 = integration_client.get("/users/profile", headers=new_headers)
        assert profile_response2.status_code == 200
    
    def test_cross_user_data_isolation(self, integration_client, mock_openai_client):
        """ユーザー間データ分離テスト"""
        users = []
        for i in range(2):
            register_data = {
                "username": f"isolationuser{i}",
                "email": f"isolation{i}@test.com",
                "password": "isolation123"
            }
            integration_client.post("/auth/register", json=register_data)
            
            login_data = {"username": f"isolationuser{i}", "password": "isolation123"}
            login_response = integration_client.post("/auth/login", json=login_data)
            token = login_response.json()["access_token"]
            users.append({"token": token, "id": i})
        
        headers1 = {"Authorization": f"Bearer {users[0]['token']}"}
        transcript_data = {"transcript": "ユーザー1の秘密会議", "title": "機密会議"}
        response1 = integration_client.post("/minutes/generate", json=transcript_data, headers=headers1)
        minutes_id = response1.json()["id"]
        
        headers2 = {"Authorization": f"Bearer {users[1]['token']}"}
        response2 = integration_client.get(f"/minutes/{minutes_id}", headers=headers2)
        assert response2.status_code == 404
        
        history_response = integration_client.get("/minutes/history", headers=headers2)
        assert len(history_response.json()["minutes"]) == 0
    
    def test_invalid_token_handling(self, integration_client):
        """無効トークンハンドリングテスト"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = integration_client.get("/users/profile", headers=invalid_headers)
        assert response.status_code == 401
        
        response2 = integration_client.get("/minutes/history", headers=invalid_headers)
        assert response2.status_code == 401
    
    def test_unauthorized_access_attempts(self, integration_client):
        """未認証アクセス試行テスト"""
        protected_endpoints = [
            ("/users/profile", "GET"),
            ("/minutes/history", "GET"),
            ("/minutes/generate", "POST")
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = integration_client.get(endpoint)
            else:
                response = integration_client.post(endpoint, json={})
            
            assert response.status_code == 401
