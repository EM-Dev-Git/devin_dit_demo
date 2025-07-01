import logging
import os
import json
from datetime import datetime
from typing import Any, Dict

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "app.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_request(endpoint: str, user_id: int = None, processing_time: float = None, **kwargs):
    logger = get_logger("request_logger")
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "user_id": user_id,
        "processing_time": processing_time,
        **kwargs
    }
    
    logger.info(f"Request processed: {json.dumps(log_data)}")

def log_error(error_message: str, endpoint: str = None, user_id: int = None, **kwargs):
    logger = get_logger("error_logger")
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": error_message,
        "endpoint": endpoint,
        "user_id": user_id,
        **kwargs
    }
    
    logger.error(f"Error occurred: {json.dumps(log_data)}")

def log_auth_event(event_type: str, username: str = None, success: bool = True, **kwargs):
    logger = get_logger("auth_logger")
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "username": username,
        "success": success,
        **kwargs
    }
    
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"Auth event: {json.dumps(log_data)}")
