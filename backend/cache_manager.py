"""
Cache Manager for PLC Code Generation
Stores generated code in memory with auto-cleanup
No disk I/O - saves space
"""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading


class CodeCache:
    """In-memory cache for generated code with automatic cleanup"""
    
    def __init__(self, max_age_seconds: int = 3600, cleanup_interval: int = 300):
        """
        Initialize cache manager
        
        Args:
            max_age_seconds: How long to keep cached code (default 1 hour)
            cleanup_interval: How often to run cleanup (default 5 minutes)
        """
        self.cache: Dict[str, dict] = {}
        self.max_age = max_age_seconds
        self.cleanup_interval = cleanup_interval
        self._cleanup_thread = None
        self._stop_cleanup = False
        self.start_cleanup_thread()
    
    def set(self, key: str, code: str, metadata: dict = None) -> str:
        """
        Store code in cache
        
        Args:
            key: Cache key
            code: Generated code
            metadata: Additional info (language, brand, requirement)
            
        Returns:
            Cache key
        """
        self.cache[key] = {
            "code": code,
            "timestamp": time.time(),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        return key
    
    def get(self, key: str) -> Optional[str]:
        """Retrieve code from cache"""
        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry["timestamp"]
            
            if age < self.max_age:
                return entry["code"]
            else:
                del self.cache[key]
                return None
        return None
    
    def get_with_metadata(self, key: str) -> Optional[dict]:
        """Get code with metadata"""
        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry["timestamp"]
            
            if age < self.max_age:
                return {
                    "code": entry["code"],
                    "metadata": entry["metadata"],
                    "created_at": entry["created_at"],
                    "age_seconds": age
                }
            else:
                del self.cache[key]
                return None
        return None
    
    def cleanup(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.max_age
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def start_cleanup_thread(self):
        """Start background cleanup thread"""
        def run_cleanup():
            while not self._stop_cleanup:
                time.sleep(self.cleanup_interval)
                if not self._stop_cleanup:
                    removed = self.cleanup()
                    if removed > 0:
                        print(f"[Cache] Cleaned up {removed} expired entries")
        
        self._cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def stop_cleanup(self):
        """Stop background cleanup thread"""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "cached_items": len(self.cache),
            "max_age_seconds": self.max_age,
            "cleanup_interval_seconds": self.cleanup_interval,
            "cache_keys": list(self.cache.keys())
        }
    
    def clear(self):
        """Clear all cache"""
        count = len(self.cache)
        self.cache.clear()
        return count


# Global cache instance
code_cache = CodeCache(max_age_seconds=3600, cleanup_interval=300)  # 1 hour retention, 5 min cleanup
