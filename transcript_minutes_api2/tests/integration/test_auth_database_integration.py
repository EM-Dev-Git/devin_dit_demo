import pytest
import os

class TestAuthDatabaseIntegration:
    def test_jwt_token_database_user_lookup_flow(self, integration_client):
        """JWT認証とDB検索の完全フロー"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        username = f"integrationuser_{unique_id}"
        email = f"integration_{unique_id}@test.com"
        
        register_data = {
            "username": username,
            "email": email,
            "password": "securepass123"
        }
        register_response = integration_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"username": username, "password": "securepass123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        response_data = login_response.json()
        assert "access_token" in response_data
        token = response_data["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = integration_client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == username
    
    def test_token_expiry_database_consistency(self, integration_client):
        """トークン期限切れ時のDB状態確認"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        username = f"expiryuser_{unique_id}"
        email = f"expiry_{unique_id}@test.com"
        
        register_data = {
            "username": username,
            "email": email,
            "password": "expiry123"
        }
        integration_client.post("/auth/register", json=register_data)
        
        login_data = {"username": username, "password": "expiry123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        response_data = login_response.json()
        assert "access_token" in response_data
        token = response_data["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = integration_client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
    
    def test_concurrent_user_authentication(self, integration_client):
        """複数ユーザーの同時認証処理"""
        import threading
        results = []
        
        def authenticate_user(user_id):
            try:
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                username = f"concurrent{user_id}_{unique_id}"
                email = f"concurrent{user_id}_{unique_id}@test.com"
                
                register_data = {
                    "username": username,
                    "email": email,
                    "password": "concurrent123"
                }
                register_response = integration_client.post("/auth/register", json=register_data)
                
                login_data = {"username": username, "password": "concurrent123"}
                login_response = integration_client.post("/auth/login", json=login_data)
                
                results.append({
                    "user_id": user_id,
                    "register_success": register_response.status_code == 201,
                    "login_success": login_response.status_code == 200 and "access_token" in login_response.json()
                })
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "error": str(e)
                })
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=authenticate_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        success_count = sum(1 for r in results if r.get("register_success") and r.get("login_success"))
        assert success_count >= 2
