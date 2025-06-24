import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt

from app.modules.auth_handler import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, authenticate_user, create_user, get_current_user
)
from app.modules.database import User

class TestAuthHandler:
    def test_verify_password_correct(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_get_password_hash(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_create_access_token_default_expiry(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        from app.modules.auth_handler import SECRET_KEY, ALGORITHM
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded
    
    def test_create_access_token_custom_expiry(self):
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        from app.modules.auth_handler import SECRET_KEY, ALGORITHM
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_time = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_time).total_seconds()) < 60
    
    def test_verify_token_valid(self):
        from fastapi import HTTPException
        data = {"sub": "testuser"}
        token = create_access_token(data)
        credentials_exception = HTTPException(status_code=401, detail="Invalid token")
        
        token_data = verify_token(token, credentials_exception)
        assert token_data.username == "testuser"
    
    def test_verify_token_invalid(self):
        from fastapi import HTTPException
        invalid_token = "invalid.token.here"
        credentials_exception = HTTPException(status_code=401, detail="Invalid token")
        
        with pytest.raises(HTTPException):
            verify_token(invalid_token, credentials_exception)
    
    def test_verify_token_expired(self):
        from fastapi import HTTPException
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        credentials_exception = HTTPException(status_code=401, detail="Invalid token")
        
        with pytest.raises(HTTPException):
            verify_token(token, credentials_exception)
    
    def test_authenticate_user_success(self, test_db, test_user, test_user_data):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = authenticate_user(db, test_user_data["username"], test_user_data["password"])
        
        assert user is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        
        db.close()
    
    def test_authenticate_user_wrong_username(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = authenticate_user(db, "nonexistent", "password123")
        
        assert user is False
        
        db.close()
    
    def test_authenticate_user_wrong_password(self, test_db, test_user):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = authenticate_user(db, test_user.username, "wrongpassword")
        
        assert user is False
        
        db.close()
    
    def test_create_user_success(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = create_user(db, "newuser", "newuser@example.com", "newpassword123")
        
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.hashed_password != "newpassword123"
        assert verify_password("newpassword123", user.hashed_password)
        
        db.close()
    
    def test_create_user_duplicate_username(self, test_db, test_user):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        with pytest.raises(Exception):
            create_user(db, test_user.username, "different@example.com", "password123")
        
        db.close()
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_db, test_user):
        from fastapi.security import HTTPAuthorizationCredentials
        from unittest.mock import MagicMock
        
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        token = create_access_token(data={"sub": test_user.username})
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        user = await get_current_user(mock_credentials, db)
        
        assert user is not None
        assert user.username == test_user.username
        assert user.email == test_user.email
        
        db.close()
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_db):
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        
        with pytest.raises(HTTPException):
            await get_current_user(mock_credentials, db)
        
        db.close()
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, test_db):
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        token = create_access_token(data={"sub": "nonexistent"})
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        with pytest.raises(HTTPException):
            await get_current_user(mock_credentials, db)
        
        db.close()
    
    def test_password_hash_different_each_time(self):
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
