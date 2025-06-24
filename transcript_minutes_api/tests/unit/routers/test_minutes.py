import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock

class TestMinutesRouter:
    def test_generate_minutes_success(self, client, auth_headers, mock_openai_client):
        minutes_data = {
            "transcript": "This is a test meeting transcript",
            "title": "Test Meeting"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["title"] == "Test Meeting"
        assert response_data["transcript"] == "This is a test meeting transcript"
        assert "generated_minutes" in response_data
        assert "id" in response_data
        assert "created_at" in response_data
    
    def test_generate_minutes_without_title(self, client, auth_headers, mock_openai_client):
        minutes_data = {
            "transcript": "This is a test meeting transcript"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["title"] == "Generated Meeting Minutes"
        assert response_data["transcript"] == "This is a test meeting transcript"
    
    def test_generate_minutes_unauthorized(self, client):
        minutes_data = {
            "transcript": "This is a test meeting transcript",
            "title": "Test Meeting"
        }
        response = client.post("/minutes/generate", json=minutes_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_generate_minutes_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        minutes_data = {
            "transcript": "This is a test meeting transcript",
            "title": "Test Meeting"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_generate_minutes_missing_transcript(self, client, auth_headers):
        minutes_data = {
            "title": "Test Meeting"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.modules.openai_client.generate_meeting_minutes')
    def test_generate_minutes_openai_error(self, mock_generate, client, auth_headers):
        mock_generate.side_effect = Exception("OpenAI API Error")
        
        minutes_data = {
            "transcript": "This is a test meeting transcript",
            "title": "Test Meeting"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to generate meeting minutes" in response.json()["detail"]
    
    def test_get_minutes_history_success(self, client, auth_headers, test_minutes):
        response = client.get("/minutes/history", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) >= 1
        assert response_data[0]["title"] == test_minutes.title
    
    def test_get_minutes_history_with_pagination(self, client, auth_headers):
        response = client.get("/minutes/history?skip=0&limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
    
    def test_get_minutes_history_unauthorized(self, client):
        response = client.get("/minutes/history")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_minutes_by_id_success(self, client, auth_headers, test_minutes):
        response = client.get(f"/minutes/{test_minutes.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == test_minutes.id
        assert response_data["title"] == test_minutes.title
        assert response_data["transcript"] == test_minutes.transcript
    
    def test_get_minutes_by_id_not_found(self, client, auth_headers):
        response = client.get("/minutes/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Meeting minutes not found" in response.json()["detail"]
    
    def test_get_minutes_by_id_unauthorized(self, client, test_minutes):
        response = client.get(f"/minutes/{test_minutes.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_minutes_by_id_different_user(self, client, test_db, test_minutes):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        from app.modules.database import User
        from app.modules.auth_handler import get_password_hash, create_access_token
        
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        
        other_token = create_access_token(data={"sub": other_user.username})
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        response = client.get(f"/minutes/{test_minutes.id}", headers=other_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        db.close()
