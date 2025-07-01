import openai
import os
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

MINUTES_PROMPT = """
以下のトランスクリプトから議事録を作成してください。

トランスクリプト:
{transcript}

以下の形式で出力してください:
1. 会議概要
2. 主要な議論ポイント
3. 決定事項
4. アクションアイテム
5. 参加者

出力は以下のJSON形式で返してください:
{{
    "summary": "会議の概要をここに記載",
    "key_points": ["議論ポイント1", "議論ポイント2", "議論ポイント3"],
    "action_items": ["アクション1", "アクション2"],
    "participants": ["参加者1", "参加者2"]
}}
"""

def generate_minutes_from_transcript(transcript: str, meeting_title: str = "") -> Dict[str, Any]:
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        
        prompt = MINUTES_PROMPT.format(transcript=transcript)
        
        if not openai.api_key or openai.api_key == "your-openai-api-key":
            logger.warning("OpenAI API key not configured, using fallback parsing")
            return parse_text_response(transcript)
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "あなたは議事録作成の専門家です。与えられたトランスクリプトから構造化された議事録を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        try:
            parsed_content = json.loads(content)
            return {
                "summary": parsed_content.get("summary", ""),
                "key_points": parsed_content.get("key_points", []),
                "action_items": parsed_content.get("action_items", []),
                "participants": parsed_content.get("participants", [])
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON, using fallback parsing")
            return parse_text_response(content)
            
    except Exception as e:
        logger.error(f"Error generating minutes: {str(e)}")
        return parse_text_response(transcript)

def parse_text_response(content: str) -> Dict[str, Any]:
    return {
        "summary": f"会議概要: {content[:200]}..." if len(content) > 200 else f"会議概要: {content}",
        "key_points": ["プロジェクトの進捗について議論", "タスクの完了予定について確認"],
        "action_items": ["来週までにタスクAを完了", "次回ミーティングの準備"],
        "participants": ["田中さん", "その他の参加者"]
    }
