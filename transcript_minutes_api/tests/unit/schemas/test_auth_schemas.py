import pytest
from pydantic import ValidationError
from app.schemas.auth import UserBase, UserCreate, UserResponse, UserLogin, Token, TokenData

class TestAuthSchemas:
    def test_user_base_valid(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        user = UserBase(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_user_base_invalid_email(self):
        user_data = {
            "username": "testuser",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError):
            UserBase(**user_data)
    
    def test_user_base_missing_fields(self):
        user_data = {
            "username": "testuser"
        }
        
        with pytest.raises(ValidationError):
            UserBase(**user_data)
    
    def test_user_create_valid(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "securepass123"
    
    def test_user_create_missing_password(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_response_valid(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "id": 1,
            "created_at": "2023-01-01T00:00:00"
        }
        user = UserResponse(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id == 1
        assert user.created_at == "2023-01-01T00:00:00"
    
    def test_user_response_missing_id(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2023-01-01T00:00:00"
        }
        
        with pytest.raises(ValidationError):
            UserResponse(**user_data)
    
    def test_user_login_valid(self):
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        login = UserLogin(**login_data)
        
        assert login.username == "testuser"
        assert login.password == "password123"
    
    def test_user_login_missing_fields(self):
        login_data = {
            "username": "testuser"
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**login_data)
    
    def test_token_valid(self):
        token_data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            "token_type": "bearer"
        }
        token = Token(**token_data)
        
        assert token.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        assert token.token_type == "bearer"
    
    def test_token_missing_fields(self):
        token_data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        }
        
        with pytest.raises(ValidationError):
            Token(**token_data)
    
    def test_token_data_valid(self):
        token_data = {
            "username": "testuser"
        }
        token = TokenData(**token_data)
        
        assert token.username == "testuser"
    
    def test_token_data_optional_username(self):
        token = TokenData()
        
        assert token.username is None
    
    def test_token_data_none_username(self):
        token_data = {
            "username": None
        }
        token = TokenData(**token_data)
        
        assert token.username is None
    
    def test_user_base_empty_username(self):
        user_data = {
            "username": "",
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserBase(**user_data)
    
    def test_user_base_whitespace_username(self):
        user_data = {
            "username": "   ",
            "email": "test@example.com"
        }
        user = UserBase(**user_data)
        
        assert user.username == "   "
    
    def test_user_create_empty_password(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": ""
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_response_invalid_id_type(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "id": "not_an_integer",
            "created_at": "2023-01-01T00:00:00"
        }
        
        with pytest.raises(ValidationError):
            UserResponse(**user_data)
