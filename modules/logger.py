import logging
import os
from datetime import datetime

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

def get_logger(name: str):
    return logging.getLogger(name)

def log_request(endpoint: str, user_id: int = None, processing_time: float = None):
    logger = get_logger("api_requests")
    message = f"Endpoint: {endpoint}"
    if user_id:
        message += f" | User ID: {user_id}"
    if processing_time:
        message += f" | Processing time: {processing_time:.2f}s"
    logger.info(message)
