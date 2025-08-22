"""
Logging utilities for ETL workflows
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logger(name: str, 
                level: int = logging.INFO,
                log_file: Optional[str] = None,
                console_output: bool = True) -> logging.Logger:
    """
    Set up a logger with consistent formatting and output options.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional file path for logging
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_etl_logger(name: str, workflow_name: str = None) -> logging.Logger:
    """
    Get a logger specifically configured for ETL workflows.
    
    Args:
        name: Logger name
        workflow_name: Optional workflow name for context
        
    Returns:
        Configured ETL logger
    """
    # Create logs directory in project root
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Generate log filename
    if workflow_name:
        log_file = logs_dir / f"{workflow_name}_{name}.log"
    else:
        log_file = logs_dir / f"{name}.log"
    
    return setup_logger(name, log_file=str(log_file))
