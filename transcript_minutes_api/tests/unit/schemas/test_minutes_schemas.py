import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.minutes import MinutesBase, MinutesCreate, MinutesResponse, MinutesGenerate

class TestMinutesSchemas:
    def test_minutes_base_valid_with_title(self):
        minutes_data = {
            "title": "Test Meeting",
            "transcript": "This is a test transcript"
        }
        minutes = MinutesBase(**minutes_data)
        
        assert minutes.title == "Test Meeting"
        assert minutes.transcript == "This is a test transcript"
    
    def test_minutes_base_valid_without_title(self):
        minutes_data = {
            "transcript": "This is a test transcript"
        }
        minutes = MinutesBase(**minutes_data)
        
        assert minutes.title is None
        assert minutes.transcript == "This is a test transcript"
    
    def test_minutes_base_missing_transcript(self):
        minutes_data = {
            "title": "Test Meeting"
        }
        
        with pytest.raises(ValidationError):
            MinutesBase(**minutes_data)
    
    def test_minutes_base_empty_transcript(self):
        minutes_data = {
            "title": "Test Meeting",
            "transcript": ""
        }
        
        with pytest.raises(ValidationError):
            MinutesBase(**minutes_data)
    
    def test_minutes_create_inherits_from_base(self):
        minutes_data = {
            "title": "Test Meeting",
            "transcript": "This is a test transcript"
        }
        minutes = MinutesCreate(**minutes_data)
        
        assert minutes.title == "Test Meeting"
        assert minutes.transcript == "This is a test transcript"
        assert isinstance(minutes, MinutesBase)
    
    def test_minutes_response_valid(self):
        minutes_data = {
            "id": 1,
            "user_id": 1,
            "title": "Test Meeting",
            "transcript": "This is a test transcript",
            "generated_minutes": "Generated meeting minutes",
            "created_at": datetime.now()
        }
        minutes = MinutesResponse(**minutes_data)
        
        assert minutes.id == 1
        assert minutes.user_id == 1
        assert minutes.title == "Test Meeting"
        assert minutes.transcript == "This is a test transcript"
        assert minutes.generated_minutes == "Generated meeting minutes"
        assert isinstance(minutes.created_at, datetime)
    
    def test_minutes_response_missing_required_fields(self):
        minutes_data = {
            "title": "Test Meeting",
            "transcript": "This is a test transcript"
        }
        
        with pytest.raises(ValidationError):
            MinutesResponse(**minutes_data)
    
    def test_minutes_response_invalid_id_type(self):
        minutes_data = {
            "id": "not_an_integer",
            "user_id": 1,
            "title": "Test Meeting",
            "transcript": "This is a test transcript",
            "generated_minutes": "Generated meeting minutes",
            "created_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            MinutesResponse(**minutes_data)
    
    def test_minutes_response_invalid_user_id_type(self):
        minutes_data = {
            "id": 1,
            "user_id": "not_an_integer",
            "title": "Test Meeting",
            "transcript": "This is a test transcript",
            "generated_minutes": "Generated meeting minutes",
            "created_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            MinutesResponse(**minutes_data)
    
    def test_minutes_generate_valid_with_title(self):
        minutes_data = {
            "transcript": "This is a test transcript",
            "title": "Test Meeting"
        }
        minutes = MinutesGenerate(**minutes_data)
        
        assert minutes.transcript == "This is a test transcript"
        assert minutes.title == "Test Meeting"
    
    def test_minutes_generate_valid_without_title(self):
        minutes_data = {
            "transcript": "This is a test transcript"
        }
        minutes = MinutesGenerate(**minutes_data)
        
        assert minutes.transcript == "This is a test transcript"
        assert minutes.title is None
    
    def test_minutes_generate_missing_transcript(self):
        minutes_data = {
            "title": "Test Meeting"
        }
        
        with pytest.raises(ValidationError):
            MinutesGenerate(**minutes_data)
    
    def test_minutes_generate_empty_transcript(self):
        minutes_data = {
            "transcript": "",
            "title": "Test Meeting"
        }
        
        with pytest.raises(ValidationError):
            MinutesGenerate(**minutes_data)
    
    def test_minutes_response_none_title(self):
        minutes_data = {
            "id": 1,
            "user_id": 1,
            "title": None,
            "transcript": "This is a test transcript",
            "generated_minutes": "Generated meeting minutes",
            "created_at": datetime.now()
        }
        minutes = MinutesResponse(**minutes_data)
        
        assert minutes.title is None
    
    def test_minutes_base_long_transcript(self):
        long_transcript = "This is a very long transcript. " * 1000
        minutes_data = {
            "title": "Long Meeting",
            "transcript": long_transcript
        }
        minutes = MinutesBase(**minutes_data)
        
        assert minutes.transcript == long_transcript
    
    def test_minutes_response_empty_generated_minutes(self):
        minutes_data = {
            "id": 1,
            "user_id": 1,
            "title": "Test Meeting",
            "transcript": "This is a test transcript",
            "generated_minutes": "",
            "created_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            MinutesResponse(**minutes_data)
    
    def test_minutes_generate_special_characters(self):
        minutes_data = {
            "transcript": "Meeting with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`",
            "title": "Special Chars Meeting"
        }
        minutes = MinutesGenerate(**minutes_data)
        
        assert minutes.transcript == "Meeting with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        assert minutes.title == "Special Chars Meeting"
