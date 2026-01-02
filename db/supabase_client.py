"""Supabase client management for database and edge functions."""

import os

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions


class SupabaseClient:
    """Singleton Supabase client manager.
    
    Environment variables required:
        SUPABASE_URL: Your Supabase project URL (e.g., https://xxx.supabase.co)
        SUPABASE_ANON_KEY: Your Supabase anonymous/public key
        SUPABASE_SERVICE_KEY: (Optional) Service role key for admin operations
    """
    
    _client: Client | None = None
    _admin_client: Client | None = None
    
    @classmethod
    def _get_url(cls) -> str:
        """Get Supabase URL from environment."""
        url = os.getenv("SUPABASE_URL")
        if not url:
            raise ValueError("SUPABASE_URL environment variable not set")
        return url
    
    @classmethod
    def _get_anon_key(cls) -> str:
        """Get Supabase anonymous key from environment."""
        key = os.getenv("SUPABASE_ANON_KEY")
        if not key:
            raise ValueError("SUPABASE_ANON_KEY environment variable not set")
        return key
    
    @classmethod
    def _get_service_key(cls) -> str | None:
        """Get Supabase service role key from environment (optional)."""
        return os.getenv("SUPABASE_SERVICE_KEY")
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create the Supabase client using anon key.
        
        Use this for regular operations that should respect RLS policies.
        """
        if cls._client is None:
            cls._client = create_client(
                cls._get_url(),
                cls._get_anon_key(),
                options=ClientOptions(
                    auto_refresh_token=True,
                    persist_session=False,
                )
            )
        return cls._client
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """Get or create the Supabase client using service role key.
        
        Use this for admin operations that bypass RLS policies.
        Requires SUPABASE_SERVICE_KEY to be set.
        """
        if cls._admin_client is None:
            service_key = cls._get_service_key()
            if not service_key:
                raise ValueError(
                    "SUPABASE_SERVICE_KEY environment variable not set. "
                    "Required for admin operations."
                )
            cls._admin_client = create_client(
                cls._get_url(),
                service_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False,
                )
            )
        return cls._admin_client
    
    @classmethod
    def reset(cls) -> None:
        """Reset clients (useful for testing or reconnection)."""
        cls._client = None
        cls._admin_client = None


# Convenience functions for quick access
def get_supabase() -> Client:
    """Get the default Supabase client."""
    return SupabaseClient.get_client()


def get_supabase_admin() -> Client:
    """Get the admin Supabase client (bypasses RLS)."""
    return SupabaseClient.get_admin_client()

