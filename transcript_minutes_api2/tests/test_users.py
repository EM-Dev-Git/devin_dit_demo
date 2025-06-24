import pytest
from fastapi import status

class TestUserProfile:
    def test_get_profile_success(self, client, auth_headers, test_user):
        response = client.get("/users/profile", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_get_profile_unauthorized(self, client):
        response = client.get("/users/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/profile", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestUserProfileUpdate:
    def test_update_profile_username_success(self, client, auth_headers, test_user):
        update_data = {"username": "updateduser"}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == test_user.email

    def test_update_profile_email_success(self, client, auth_headers, test_user):
        update_data = {"email": "updated@example.com"}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == "updated@example.com"

    def test_update_profile_both_fields_success(self, client, auth_headers):
        update_data = {
            "username": "newusername",
            "email": "newemail@example.com"
        }
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newusername"
        assert data["email"] == "newemail@example.com"

    def test_update_profile_duplicate_username(self, client, auth_headers, test_user2):
        update_data = {"username": test_user2.username}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_update_profile_duplicate_email(self, client, auth_headers, test_user2):
        update_data = {"email": test_user2.email}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_update_profile_invalid_username_too_short(self, client, auth_headers):
        update_data = {"username": "ab"}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_profile_invalid_username_special_chars(self, client, auth_headers):
        update_data = {"username": "user@name"}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_profile_invalid_email(self, client, auth_headers):
        update_data = {"email": "invalid-email"}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_profile_unauthorized(self, client):
        update_data = {"username": "newusername"}
        response = client.put("/users/profile", json=update_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_empty_data(self, client, auth_headers):
        update_data = {}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_update_profile_null_values(self, client, auth_headers):
        update_data = {"username": None, "email": None}
        response = client.put("/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
