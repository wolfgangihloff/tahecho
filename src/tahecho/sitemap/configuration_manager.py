"""Configuration manager for sitemap agents."""

import os
import json
import yaml
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages configuration for sitemap agents."""
    
    def __init__(self):
        """Initialize configuration manager."""
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        self._enabled = self._get_bool_env('SITEMAP_AGENTS_ENABLED', False)
        self._yaml_config = {}
        
        if self._enabled:
            self._validate_required_config()
            self._load_config()
    
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default {default}")
            return default
    
    def _validate_required_config(self):
        """Validate that required configuration is present."""
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        required_keys = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
    
    def _load_config(self):
        """Load configuration from environment variables."""
        self._supabase_url = os.getenv('SUPABASE_URL')
        self._supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self._supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Sitemap configuration
        sitemap_urls = os.getenv('SITEMAP_URLS', '')
        self._sitemap_urls = [url.strip() for url in sitemap_urls.split(',') if url.strip()]
        
        self._requests_per_second = self._get_int_env('SITEMAP_REQUESTS_PER_SECOND', 2)
        self._max_pages = self._get_int_env('SITEMAP_MAX_PAGES', 100)
        self._verify_ssl = self._get_bool_env('SITEMAP_VERIFY_SSL', False)
        
        # Embedding configuration
        self._embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self._embedding_dimension = self._get_int_env('EMBEDDING_DIMENSION', 1536)
        
        # Processing configuration
        self._async_enabled = self._get_bool_env('ASYNC_PROCESSING_ENABLED', True)
        self._batch_size = self._get_int_env('PROCESSING_BATCH_SIZE', 10)
        self._cleanup_after_upload = self._get_bool_env('CLEANUP_AFTER_UPLOAD', True)
        
        # Load sitemap-specific configuration
        self._load_sitemap_config()
    
    def _load_sitemap_config(self):
        """Load sitemap-specific configuration."""
        sitemap_config_str = os.getenv('SITEMAP_CONFIG', '{}')
        try:
            self._sitemap_config = json.loads(sitemap_config_str)
        except json.JSONDecodeError:
            logger.warning("Invalid SITEMAP_CONFIG JSON, using empty config")
            self._sitemap_config = {}
    
    def is_enabled(self) -> bool:
        """Check if sitemap agents are enabled."""
        return self._enabled
    
    def get_sitemap_urls(self) -> List[str]:
        """Get list of sitemap URLs."""
        return self._sitemap_urls.copy()
    
    def get_requests_per_second(self) -> int:
        """Get requests per second limit."""
        return self._requests_per_second
    
    def get_max_pages(self) -> int:
        """Get maximum pages to scrape."""
        return self._max_pages
    
    def get_supabase_url(self) -> str:
        """Get Supabase URL."""
        return self._supabase_url
    
    def get_supabase_anon_key(self) -> str:
        """Get Supabase anonymous key."""
        return self._supabase_anon_key
    
    def get_supabase_service_key(self) -> Optional[str]:
        """Get Supabase service role key."""
        return self._supabase_service_key
    
    def get_sitemap_config(self, sitemap_url: str) -> Optional[Dict[str, Any]]:
        """Get sitemap-specific configuration."""
        return self._sitemap_config.get(sitemap_url)
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration."""
        return {
            "model": self._embedding_model,
            "dimension": self._embedding_dimension
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return {
            "async_enabled": self._async_enabled,
            "batch_size": self._batch_size,
            "cleanup_after_upload": self._cleanup_after_upload,
            "verify_ssl": self._verify_ssl
        }
    
    def load_yaml_config(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                self._yaml_config = yaml.safe_load(file)
            logger.info(f"Loaded YAML configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load YAML configuration from {config_path}: {e}")
            self._yaml_config = {}
    
    def get_yaml_config(self) -> Dict[str, Any]:
        """Get YAML configuration."""
        return self._yaml_config.copy()
    
    def get_sitemap_domain(self, sitemap_url: str) -> str:
        """Get domain from sitemap URL."""
        return urlparse(sitemap_url).netloc
    
    def validate_sitemap_url(self, sitemap_url: str) -> bool:
        """Validate sitemap URL format."""
        try:
            parsed = urlparse(sitemap_url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False 