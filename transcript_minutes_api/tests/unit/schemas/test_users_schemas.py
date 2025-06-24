import pytest
from pydantic import ValidationError
from app.schemas.users import UserProfile, UserProfileUpdate

class TestUsersSchemas:
    def test_user_profile_valid(self):
        profile_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        profile = UserProfile(**profile_data)
        
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"
    
    def test_user_profile_invalid_email(self):
        profile_data = {
            "username": "testuser",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError):
            UserProfile(**profile_data)
    
    def test_user_profile_missing_username(self):
        profile_data = {
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserProfile(**profile_data)
    
    def test_user_profile_missing_email(self):
        profile_data = {
            "username": "testuser"
        }
        
        with pytest.raises(ValidationError):
            UserProfile(**profile_data)
    
    def test_user_profile_empty_username(self):
        profile_data = {
            "username": "",
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserProfile(**profile_data)
    
    def test_user_profile_update_both_fields(self):
        update_data = {
            "username": "newusername",
            "email": "newemail@example.com"
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username == "newusername"
        assert update.email == "newemail@example.com"
    
    def test_user_profile_update_username_only(self):
        update_data = {
            "username": "newusername"
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username == "newusername"
        assert update.email is None
    
    def test_user_profile_update_email_only(self):
        update_data = {
            "email": "newemail@example.com"
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username is None
        assert update.email == "newemail@example.com"
    
    def test_user_profile_update_empty_data(self):
        update_data = {}
        update = UserProfileUpdate(**update_data)
        
        assert update.username is None
        assert update.email is None
    
    def test_user_profile_update_invalid_email(self):
        update_data = {
            "username": "newusername",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError):
            UserProfileUpdate(**update_data)
    
    def test_user_profile_update_empty_username(self):
        update_data = {
            "username": "",
            "email": "newemail@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserProfileUpdate(**update_data)
    
    def test_user_profile_update_none_values(self):
        update_data = {
            "username": None,
            "email": None
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username is None
        assert update.email is None
    
    def test_user_profile_special_characters_username(self):
        profile_data = {
            "username": "test_user-123",
            "email": "test@example.com"
        }
        profile = UserProfile(**profile_data)
        
        assert profile.username == "test_user-123"
    
    def test_user_profile_update_special_characters_username(self):
        update_data = {
            "username": "new_user-456"
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username == "new_user-456"
    
    def test_user_profile_long_username(self):
        long_username = "a" * 100
        profile_data = {
            "username": long_username,
            "email": "test@example.com"
        }
        profile = UserProfile(**profile_data)
        
        assert profile.username == long_username
    
    def test_user_profile_update_long_username(self):
        long_username = "b" * 100
        update_data = {
            "username": long_username
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.username == long_username
    
    def test_user_profile_complex_email(self):
        profile_data = {
            "username": "testuser",
            "email": "test.user+tag@example-domain.co.uk"
        }
        profile = UserProfile(**profile_data)
        
        assert profile.email == "test.user+tag@example-domain.co.uk"
    
    def test_user_profile_update_complex_email(self):
        update_data = {
            "email": "new.user+tag@example-domain.co.uk"
        }
        update = UserProfileUpdate(**update_data)
        
        assert update.email == "new.user+tag@example-domain.co.uk"
