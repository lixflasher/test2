import logging
import sys
from pathlib import Path

def setup_logger(name="qidian_scraper", log_file="scraper.log", level=logging.INFO):
    # Create logs directory if it doesn't exist
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    file_handler = logging.FileHandler(log_path / log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
