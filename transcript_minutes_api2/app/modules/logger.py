import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "app.log")

def setup_logger():
    logger = logging.getLogger("transcript_minutes_api")
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def log_api_call(endpoint: str, user_id: int = None, duration: float = None, error: str = None):
    if error:
        logger.error(f"API Error - Endpoint: {endpoint}, User: {user_id}, Error: {error}")
    else:
        logger.info(f"API Call - Endpoint: {endpoint}, User: {user_id}, Duration: {duration}s")

def log_openai_call(user_id: int, tokens_used: int = None, error: str = None):
    if error:
        logger.error(f"OpenAI Error - User: {user_id}, Error: {error}")
    else:
        logger.info(f"OpenAI Call - User: {user_id}, Tokens: {tokens_used}")
