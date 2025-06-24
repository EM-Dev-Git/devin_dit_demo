import pytest
from fastapi import status
from app.modules.database import User
from app.modules.auth_handler import verify_password

class TestAuthRegister:
    def test_register_success(self, client):
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_register_duplicate_username(self, client, test_user):
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_username_too_short(self, client):
        user_data = {
            "username": "ab",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_username_special_chars(self, client):
        user_data = {
            "username": "user@name",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_email(self, client):
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "securepassword123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_too_short(self, client):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        user_data = {"username": "testuser"}
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestAuthLogin:
    def test_login_success(self, client, test_user):
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, client):
        login_data = {
            "username": "nonexistentuser",
            "password": "testpassword123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_invalid_password(self, client, test_user):
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_missing_username(self, client):
        login_data = {"password": "testpassword123"}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_password(self, client):
        login_data = {"username": "testuser"}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self, client):
        login_data = {"username": "", "password": ""}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestAuthRefresh:
    def test_refresh_success(self, client, auth_headers):
        response = client.post("/auth/refresh", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_missing_token(self, client):
        response = client.post("/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/auth/refresh", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_malformed_header(self, client):
        headers = {"Authorization": "invalid_format"}
        response = client.post("/auth/refresh", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
