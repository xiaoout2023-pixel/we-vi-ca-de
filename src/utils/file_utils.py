import os
import shutil
from src.utils.logger import get_logger

logger = get_logger(__name__)

def clean_directory(dir_path):
    if os.path.exists(dir_path):
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        logger.info(f"Cleaned directory: {dir_path}")

def ensure_directory(dir_path):
    os.makedirs(dir_path, exist_ok=True)

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:200]
