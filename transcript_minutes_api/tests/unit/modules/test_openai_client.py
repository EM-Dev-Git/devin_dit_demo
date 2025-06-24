import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.openai_client import generate_meeting_minutes

class TestOpenAIClient:
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_success(self, mock_openai_client):
        transcript = "This is a test meeting transcript with important points."
        title = "Test Meeting"
        
        result = await generate_meeting_minutes(transcript, title)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
        
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert len(call_args[1]["messages"]) == 2
        assert "system" in call_args[1]["messages"][0]["role"]
        assert "user" in call_args[1]["messages"][1]["role"]
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_without_title(self, mock_openai_client):
        transcript = "This is a test meeting transcript."
        
        result = await generate_meeting_minutes(transcript)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_with_title(self, mock_openai_client):
        transcript = "This is a test meeting transcript."
        title = "Important Meeting"
        
        result = await generate_meeting_minutes(transcript, title)
        
        assert result == "Generated meeting minutes content"
        
        call_args = mock_openai_client.chat.completions.create.call_args
        user_message = call_args[1]["messages"][1]["content"]
        assert "Important Meeting" in user_message
        assert transcript in user_message
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_api_error(self, mocker):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', 
                    side_effect=Exception("OpenAI API Error"))
        
        transcript = "This is a test meeting transcript."
        
        with pytest.raises(Exception) as exc_info:
            await generate_meeting_minutes(transcript)
        
        assert "OpenAI API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_empty_transcript(self, mock_openai_client):
        transcript = ""
        
        result = await generate_meeting_minutes(transcript)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_long_transcript(self, mock_openai_client):
        transcript = "This is a very long transcript. " * 1000
        title = "Long Meeting"
        
        result = await generate_meeting_minutes(transcript, title)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_special_characters(self, mock_openai_client):
        transcript = "Meeting with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        title = "Special Chars Meeting"
        
        result = await generate_meeting_minutes(transcript, title)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_unicode_content(self, mock_openai_client):
        transcript = "会議の内容です。重要なポイントがあります。"
        title = "日本語会議"
        
        result = await generate_meeting_minutes(transcript, title)
        
        assert result == "Generated meeting minutes content"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.modules.openai_client.client')
    async def test_generate_meeting_minutes_response_structure(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Custom generated content"
        mock_client.chat.completions.create.return_value = mock_response
        
        transcript = "Test transcript"
        result = await generate_meeting_minutes(transcript)
        
        assert result == "Custom generated content"
    
    @pytest.mark.asyncio
    async def test_generate_meeting_minutes_system_prompt(self, mock_openai_client):
        transcript = "Test meeting content"
        title = "Test Meeting"
        
        await generate_meeting_minutes(transcript, title)
        
        call_args = mock_openai_client.chat.completions.create.call_args
        system_message = call_args[1]["messages"][0]
        
        assert system_message["role"] == "system"
        assert "議事録" in system_message["content"]
        assert "要約" in system_message["content"]
