import pytest

class TestCompleteUserJourney:
    def test_complete_user_lifecycle(self, integration_client, mock_openai_client):
        """ユーザーライフサイクル完全テスト"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        username = f"journeyuser_{unique_id}"
        email = f"journey_{unique_id}@test.com"
        
        register_data = {
            "username": username,
            "email": email, 
            "password": "journey123"
        }
        register_response = integration_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"username": username, "password": "journey123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        response_data = login_response.json()
        assert "access_token" in response_data
        token = response_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = integration_client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == username
        
        minutes_ids = []
        for i in range(3):
            transcript_data = {
                "transcript": f"会議{i+1}のトランスクリプト内容",
                "title": f"会議{i+1}"
            }
            response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
            assert response.status_code == 201
            minutes_ids.append(response.json()["id"])
        
        history_response = integration_client.get("/minutes/history", headers=headers)
        assert history_response.status_code == 200
        assert len(history_response.json()) == 3
        
        for minutes_id in minutes_ids:
            get_response = integration_client.get(f"/minutes/{minutes_id}", headers=headers)
            assert get_response.status_code == 200
        
        update_data = {"email": f"updated_{unique_id}@test.com"}
        update_response = integration_client.put("/users/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        assert update_response.json()["email"] == f"updated_{unique_id}@test.com"
    
    def test_multi_user_isolation(self, integration_client, mock_openai_client):
        """複数ユーザーのデータ分離テスト"""
        import uuid
        users = []
        for i in range(2):
            unique_id = str(uuid.uuid4())[:8]
            username = f"user{i}_{unique_id}"
            email = f"user{i}_{unique_id}@test.com"
            
            register_data = {
                "username": username,
                "email": email,
                "password": "password123"
            }
            integration_client.post("/auth/register", json=register_data)
            
            login_data = {"username": username, "password": "password123"}
            login_response = integration_client.post("/auth/login", json=login_data)
            
            response_data = login_response.json()
            assert "access_token" in response_data
            token = response_data["access_token"]
            users.append({"token": token, "username": username})
        
        for i, user in enumerate(users):
            headers = {"Authorization": f"Bearer {user['token']}"}
            transcript_data = {
                "transcript": f"{user['username']}の会議内容",
                "title": f"{user['username']}の会議"
            }
            response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
            assert response.status_code == 201
        
        for user in users:
            headers = {"Authorization": f"Bearer {user['token']}"}
            history_response = integration_client.get("/minutes/history", headers=headers)
            assert history_response.status_code == 200
            minutes_list = history_response.json()
            assert len(minutes_list) == 1
            assert user["username"] in minutes_list[0]["title"]
