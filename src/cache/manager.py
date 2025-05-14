import time
import shutil
from pathlib import Path
from typing import Optional, Union
import streamlit as st

class CacheManager:
    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        max_size_mb: int = 500,
        app_name: str = "bim_app"
    ):
        """
        Enhanced cache manager that stores cache and downloads in tests/ and protects its own file.

        Args:
            cache_dir: Custom cache directory path (overrides default under tests/cache)
            max_size_mb: Maximum cache size in megabytes
            app_name: Application name for folder naming (currently unused)
        """
        # Path to this manager file to protect it from deletion
        self._manager_file = Path(__file__).resolve()
        # Determine project root (src/cache/manager.py -> project root)
        project_root = self._manager_file.parents[2]

        # Set cache directory under tests/cache by default
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = project_root / "tests" / "cache"

        # Set downloads directory under tests/downloads
        self.download_dir = project_root / "tests" / "downloads"

        # Size limit in bytes
        self.max_size = max_size_mb * 1024 * 1024
        self.app_name = app_name
        self._setup_done = False

    def setup(self) -> None:
        """Initialize cache and downloads directories and enforce limits."""
        # Create cache and downloads folders if they don't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        # Clean old cache files and enforce size limits
        self._clean_old_files()
        self._enforce_size_limit()
        self._setup_done = True

    def clear(self, full: bool = False) -> None:
        """
        Clear cached files while protecting manager file.

        Args:
            full: If True, clears entire cache except manager file; downloaded files remain.
        """
        # Target only cache_dir
        if full:
            for item in self.cache_dir.iterdir():
                try:
                    if item.resolve() == self._manager_file:
                        continue
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                except (OSError, PermissionError):
                    continue
        else:
            # Remove all cache files (age <= 0) except protected
            self._clean_old_files(max_age_seconds=0)

        # Clear any Streamlit cache resources
        try:
            st.cache_resource.clear()
        except Exception:
            pass

    def _clean_old_files(self, max_age_seconds: int = 86400) -> None:
        """Remove old files in cache_dir while protecting manager file."""
        now = time.time()
        for f in self.cache_dir.iterdir():
            try:
                if f.resolve() == self._manager_file or f.is_dir():
                    continue
                # Delete if older than threshold or threshold zero
                if max_age_seconds == 0 or f.stat().st_mtime < now - max_age_seconds:
                    f.unlink(missing_ok=True)
            except (OSError, PermissionError):
                continue

    def _enforce_size_limit(self) -> None:
        """Enforce cache size limit by deleting oldest files first, protecting manager file."""
        files = [f for f in self.cache_dir.iterdir() if f.is_file() and f.resolve() != self._manager_file]
        current_size = sum(f.stat().st_size for f in files)
        if current_size <= self.max_size:
            return
        # Sort files by age (oldest first)
        files.sort(key=lambda f: f.stat().st_mtime)
        target = self.max_size * 0.9
        for f in files:
            if current_size <= target:
                break
            try:
                size = f.stat().st_size
                f.unlink(missing_ok=True)
                current_size -= size
            except (OSError, PermissionError):
                continue

    # Other methods (get_cache_file, get_hashed_cache_file, cache_size, list_cached_files) remain unchanged
