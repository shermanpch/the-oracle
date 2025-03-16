import logging
import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

# Log environment setup
logger.info("Loading Supabase configuration from environment")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.critical("Supabase URL or API key missing from environment variables")
    raise ValueError("Supabase URL and API key must be set in environment variables")

# Initialize the default client with anon key
logger.info(f"Initializing default Supabase client with URL: {SUPABASE_URL[:20]}...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("Default Supabase client initialized successfully")


def get_supabase_client(
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> Client:
    """
    Returns a Supabase client, optionally authenticated with user tokens.

    Args:
        access_token: Optional JWT access token for authenticated requests
        refresh_token: Optional refresh token to use with the access token

    Returns:
        A configured Supabase client
    """
    # If no tokens provided, return the default client
    if not access_token:
        logger.info("No access token provided, using default unauthenticated client")
        return supabase

    # Log token details (safely)
    if access_token:
        token_preview = access_token[:10] if len(access_token) > 10 else "[EMPTY]"
        logger.info(
            f"Creating authenticated client with token starting with: {token_preview}..."
        )

    logger.info(f"Refresh token provided: {refresh_token is not None}")

    # Create a new client instance
    logger.debug("Creating new Supabase client instance")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Set the session with the provided tokens if both are available
        if access_token and refresh_token:
            logger.info("Setting session with both access and refresh tokens")
            try:
                client.auth.set_session(access_token, refresh_token)
                logger.debug("Session set successfully with both tokens")
            except Exception as e:
                logger.error(f"Failed to set session with both tokens: {str(e)}")
                # Continue without refresh token
        elif access_token:
            # Always set the Authorization header for postgrest even without refresh token
            logger.info("No refresh token, setting auth for postgrest only")

        # Always set the Authorization header for postgrest
        # This is the most critical part for RLS
        logger.debug("Setting auth header for PostgreSQL REST client")
        client.postgrest.auth(access_token)
        logger.debug("Auth header set successfully for PostgreSQL REST client")

        # Verify the client is authenticated
        try:
            logger.debug("Verifying client authentication")
            user_info = client.auth.get_user(access_token)
            logger.info(
                f"Successfully authenticated as user: {user_info.user.email} (ID: {user_info.user.id})"
            )
        except Exception as e:
            logger.error(f"Failed to verify user with token: {str(e)}")
            logger.warning("Will continue with potentially unverified client")

        logger.info("Authenticated Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error setting up authenticated client: {str(e)}")
        logger.warning("Falling back to default unauthenticated client")
        # If authentication fails, return the default client
        return supabase
