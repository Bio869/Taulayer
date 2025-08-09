# api/db/dependencies.py

from supabase import create_client, Client
from config import settings

# Centralized Supabase client factory for:
# 1. Single point for URL/key config
# 2. FastAPI dependency injection
# 3. Future pooling/logging/retry logic
# Avoid calling create_client(...) directly in endpoints
def get_supabase() -> Client:
    """Create a Supabase client from configured env vars."""
    return create_client(settings.supabase_url, settings.supabase_key)
