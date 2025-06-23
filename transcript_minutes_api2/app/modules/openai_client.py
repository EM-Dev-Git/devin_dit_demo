from openai import AsyncOpenAI
from typing import Optional
import os
from dotenv import load_dotenv
from app.modules.logger import logger, log_openai_call

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MINUTES_PROMPT = """
以下のトランスクリプトを基に、構造化された議事録を作成してください。

【出力形式】

【トランスクリプト】
{transcript}
"""

async def generate_minutes(transcript: str, user_id: int, title: Optional[str] = None) -> str:
    try:
        logger.info(f"Generating meeting minutes for user {user_id}, transcript length: {len(transcript)}")
        
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            raise ValueError("OpenAI API key not configured")
        
        prompt = MINUTES_PROMPT.format(transcript=transcript)
        
        if title:
            prompt = f"会議タイトル: {title}\n\n" + prompt
        
        if not client:
            raise ValueError("OpenAI client not initialized")
            
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "あなたは会議の議事録作成の専門家です。与えられたトランスクリプトから構造化された議事録を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        generated_minutes = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        
        log_openai_call(user_id, tokens_used)
        logger.info(f"Successfully generated minutes for user {user_id}, tokens used: {tokens_used}")
        
        return generated_minutes
        
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        log_openai_call(user_id, error=error_msg)
        logger.error(f"Failed to generate minutes for user {user_id}: {error_msg}")
        raise Exception(f"議事録の生成に失敗しました: {str(e)}")
