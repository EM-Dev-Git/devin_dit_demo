import pytest
from fastapi import status
from unittest.mock import patch

class TestUsersRouter:
    def test_get_user_profile_success(self, client, auth_headers, test_user):
        response = client.get("/users/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == test_user.username
        assert response_data["email"] == test_user.email
    
    def test_get_user_profile_unauthorized(self, client):
        response = client.get("/users/profile")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_user_profile_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_user_profile_username_success(self, client, auth_headers, test_user):
        update_data = {
            "username": "updateduser"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == "updateduser"
        assert response_data["email"] == test_user.email
    
    def test_update_user_profile_email_success(self, client, auth_headers, test_user):
        update_data = {
            "email": "updated@example.com"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == test_user.username
        assert response_data["email"] == "updated@example.com"
    
    def test_update_user_profile_both_fields(self, client, auth_headers):
        update_data = {
            "username": "newusername",
            "email": "newemail@example.com"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == "newusername"
        assert response_data["email"] == "newemail@example.com"
    
    def test_update_user_profile_duplicate_username(self, client, auth_headers, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        from app.modules.database import User
        from app.modules.auth_handler import get_password_hash
        
        existing_user = User(
            username="existinguser",
            email="existing@example.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(existing_user)
        db.commit()
        
        update_data = {
            "username": "existinguser"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already taken" in response.json()["detail"]
        
        db.close()
    
    def test_update_user_profile_duplicate_email(self, client, auth_headers, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        from app.modules.database import User
        from app.modules.auth_handler import get_password_hash
        
        existing_user = User(
            username="existinguser2",
            email="existing2@example.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(existing_user)
        db.commit()
        
        update_data = {
            "email": "existing2@example.com"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already taken" in response.json()["detail"]
        
        db.close()
    
    def test_update_user_profile_unauthorized(self, client):
        update_data = {
            "username": "newusername"
        }
        response = client.put("/users/profile", json=update_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_user_profile_invalid_email(self, client, auth_headers):
        update_data = {
            "email": "invalid-email"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_user_profile_empty_data(self, client, auth_headers, test_user):
        update_data = {}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == test_user.username
        assert response_data["email"] == test_user.email
    
    @patch('app.modules.database.SessionLocal')
    def test_update_user_profile_database_error(self, mock_session, client, auth_headers):
        mock_session.return_value.__enter__.return_value.commit.side_effect = Exception("Database error")
        
        update_data = {
            "username": "erroruser"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to update profile" in response.json()["detail"]
