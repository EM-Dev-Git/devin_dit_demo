import pytest
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock

from app.modules.logger import setup_logger, get_logger

class TestLogger:
    def test_setup_logger_default_config(self):
        with patch.dict(os.environ, {}, clear=True):
            setup_logger()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
    
    def test_setup_logger_custom_log_level(self):
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logger()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
    
    def test_setup_logger_invalid_log_level(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(AttributeError):
                setup_logger()
    
    def test_setup_logger_custom_log_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file_path}):
                setup_logger()
                
                test_logger = logging.getLogger("test")
                test_logger.info("Test message")
                
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    assert "Test message" in log_content
        finally:
            os.unlink(log_file_path)
    
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_calls_setup(self):
        with patch('app.modules.logger.setup_logger') as mock_setup:
            get_logger("test_module")
            mock_setup.assert_called_once()
    
    def test_get_logger_different_names(self):
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 != logger2
    
    def test_get_logger_same_name_returns_same_instance(self):
        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")
        
        assert logger1 is logger2
    
    def test_logger_format_includes_required_fields(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file_path}):
                logger = get_logger("format_test")
                logger.info("Format test message")
                
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    assert "format_test" in log_content
                    assert "INFO" in log_content
                    assert "Format test message" in log_content
                    assert "-" in log_content
        finally:
            os.unlink(log_file_path)
    
    def test_logger_handles_different_log_levels(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file_path, "LOG_LEVEL": "DEBUG"}):
                logger = get_logger("level_test")
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    assert "Debug message" in log_content
                    assert "Info message" in log_content
                    assert "Warning message" in log_content
                    assert "Error message" in log_content
        finally:
            os.unlink(log_file_path)
    
    def test_logger_respects_log_level_filtering(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file_path, "LOG_LEVEL": "WARNING"}):
                logger = get_logger("filter_test")
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    assert "Debug message" not in log_content
                    assert "Info message" not in log_content
                    assert "Warning message" in log_content
                    assert "Error message" in log_content
        finally:
            os.unlink(log_file_path)
