import pytest

class TestDataIntegrityIntegration:
    def test_foreign_key_constraints(self, integration_client, integration_db, mock_openai_client):
        """外部キー制約の統合テスト"""
        import uuid
        SessionLocal, engine = integration_db
        
        unique_id = str(uuid.uuid4())[:8]
        username = f"fkuser_{unique_id}"
        email = f"fk_{unique_id}@test.com"
        
        register_data = {"username": username, "email": email, "password": "fk123"}
        register_response = integration_client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"username": username, "password": "fk123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        transcript_data = {"transcript": "FK制約テスト", "title": "FK会議"}
        minutes_response = integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
        minutes_id = minutes_response.json()["id"]
        
        with SessionLocal() as db:
            from app.modules.database import User, Minutes
            user = db.query(User).filter(User.username == username).first()
            
            try:
                db.delete(user)
                db.commit()
                assert False, "外部キー制約が働いていない"
            except Exception:
                db.rollback()
        
        get_response = integration_client.get(f"/minutes/{minutes_id}", headers=headers)
        assert get_response.status_code == 200
    
    def test_data_validation_constraints(self, integration_client):
        """データ検証制約テスト"""
        invalid_register_data = {
            "username": "",
            "email": "invalid-email",
            "password": "123"
        }
        response = integration_client.post("/auth/register", json=invalid_register_data)
        assert response.status_code == 422
        
        valid_register_data = {"username": "validuser", "email": "valid@test.com", "password": "validpass123"}
        integration_client.post("/auth/register", json=valid_register_data)
        
        duplicate_response = integration_client.post("/auth/register", json=valid_register_data)
        assert duplicate_response.status_code == 400
    
    def test_cascade_operations(self, integration_client, integration_db, mock_openai_client):
        """カスケード操作テスト"""
        SessionLocal, engine = integration_db
        
        register_data = {"username": "cascadeuser", "email": "cascade@test.com", "password": "cascade123"}
        integration_client.post("/auth/register", json=register_data)
        
        login_data = {"username": "cascadeuser", "password": "cascade123"}
        login_response = integration_client.post("/auth/login", json=login_data)
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        for i in range(2):
            transcript_data = {"transcript": f"カスケードテスト{i}", "title": f"カスケード会議{i}"}
            integration_client.post("/minutes/generate", json=transcript_data, headers=headers)
        
        history_response = integration_client.get("/minutes/history", headers=headers)
        assert len(history_response.json()) == 2
