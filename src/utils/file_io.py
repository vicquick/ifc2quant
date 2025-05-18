from pathlib import Path
from typing import Union, Optional
import tempfile
import shutil

def safe_write_bytes(path: Union[str, Path], data: bytes) -> Path:
    """Safely write bytes to a file with atomic write pattern."""
    path = Path(path)
    temp_path = Path(tempfile.mktemp(dir=path.parent))
    
    try:
        temp_path.write_bytes(data)
        temp_path.replace(path)
        return path
    except:
        temp_path.unlink(missing_ok=True)
        raise

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists and return Path object."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path