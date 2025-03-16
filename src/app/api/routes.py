"""
API routes for the Oracle I Ching API.

This module contains all the API route definitions and handlers for the Oracle I Ching API.
"""

import logging
import time
import traceback
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from src.app.api.models import OracleRequest, OracleResponse
from src.app.core.oracle import Oracle
from src.utils.llm_handler import query_llm
from src.utils.supabase_client import get_supabase_client

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    logger.info("Root endpoint accessed")
    return {"message": "Oracle I Ching API is running"}


async def verify_jwt(
    request: Request,
    authorization: str = Header(None),
    refresh_token: str = Header(None, alias="X-Refresh-Token"),
):
    """
    Verify the JWT token from Supabase and return user info and tokens.

    Args:
        request: The FastAPI request object
        authorization: Authorization header containing the access token
        refresh_token: Optional refresh token header
    """
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"JWT verification requested from {client_host}")

    if not authorization or not authorization.startswith("Bearer "):
        logger.warning(
            f"Invalid authentication attempt from {client_host} - missing or malformed Authorization header"
        )
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )

    access_token = authorization.replace("Bearer ", "")
    token_preview = (
        access_token[:10] if access_token and len(access_token) > 10 else "[EMPTY]"
    )
    logger.info(
        f"Verifying JWT with token starting with: {token_preview} from {client_host}"
    )
    logger.info(f"Refresh token provided: {refresh_token is not None}")

    try:
        # Verify the token with Supabase
        logger.debug("Creating Supabase client for token verification")
        supabase = get_supabase_client()

        start_time = time.time()
        user = supabase.auth.get_user(access_token)
        verification_time = time.time() - start_time

        # Log the user information
        logger.info(
            f"User verified in {verification_time:.2f}s: {user.user.email} (ID: {user.user.id}) from {client_host}"
        )

        # Return both user and the tokens for later use
        return {
            "user": user,
            "access_token": access_token,  # Changed key from "token" to "access_token" for consistency
            "refresh_token": refresh_token,
        }
    except Exception as e:
        logger.error(f"JWT verification failed from {client_host}: {str(e)}")
        logger.debug(f"Token verification error details: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@router.post("/oracle", response_model=OracleResponse)
async def get_oracle_reading(
    request: Request, oracle_request: OracleRequest, auth_data=Depends(verify_jwt)
):
    """
    Get an I Ching reading based on the provided numbers and question.
    Requires authentication.
    """
    client_host = request.client.host if request.client else "unknown"
    request_id = id(request)  # Generate a unique ID for this request

    try:
        # Get user info and tokens from the dependency
        user = auth_data["user"]
        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")
        user_id = user.user.id

        logger.info(
            f"[Request {request_id}] Getting oracle reading for user: {user.user.email} from {client_host}"
        )
        logger.info(f"[Request {request_id}] Question: {oracle_request.question}")
        logger.info(
            f"[Request {request_id}] Numbers: {oracle_request.first_number}, {oracle_request.second_number}, {oracle_request.third_number}"
        )

        # Initialize the Oracle with Supabase as the data source
        logger.debug(
            f"[Request {request_id}] Initializing Oracle with Supabase data source"
        )
        oracle = Oracle(data_source="supabase")

        # Set the input values
        oracle.input(
            oracle_request.first_number,
            oracle_request.second_number,
            oracle_request.third_number,
        )

        # Convert to coordinates
        oracle.convert_to_cord()

        logger.info(
            f"[Request {request_id}] Coordinates: {oracle.get_parent_directory()}, {oracle.get_child_directory()}"
        )

        # Get the content from the parent and child directories
        logger.debug(
            f"[Request {request_id}] Fetching parent content from {oracle.get_parent_directory()}"
        )
        parent_content = oracle.get_txt_file(oracle.get_parent_directory())

        logger.debug(
            f"[Request {request_id}] Fetching child content from {oracle.get_child_directory()}"
        )
        child_content = oracle.get_txt_file(oracle.get_child_directory())

        # Get the image path
        logger.debug(
            f"[Request {request_id}] Getting image path for {oracle.get_child_directory()}"
        )
        child_image_path = oracle.get_image_path(oracle.get_child_directory())

        # Query the LLM
        logger.info(
            f"[Request {request_id}] Querying LLM for prediction in {oracle_request.language}"
        )
        start_time = time.time()
        result = query_llm(
            oracle_request.question,
            parent_content,
            child_content,
            oracle_request.language,
            "env",
        )
        llm_time = time.time() - start_time
        logger.info(f"[Request {request_id}] LLM response received in {llm_time:.2f}s")

        # Convert the Pydantic model to a dictionary
        response_dict = result.model_dump()

        # Add the image path to the response
        response_dict["image_path"] = child_image_path

        logger.info(f"[Request {request_id}] Oracle reading generated successfully")

        return response_dict

    except Exception as e:
        logger.error(f"[Request {request_id}] Error in get_oracle_reading: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    client_host = request.client.host if request.client else "unknown"
    logger.debug(f"Health check from {client_host}")
    return {"status": "healthy"}


@router.get("/languages")
async def get_languages(request: Request):
    """Get the available languages for the Oracle."""
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Languages requested from {client_host}")
    return {"languages": ["English", "Chinese"]}


@router.get("/user/readings", response_model=List[Dict[str, Any]])
async def get_user_readings(request: Request, auth_data=Depends(verify_jwt)):
    """
    Get the reading history for the authenticated user.
    """
    client_host = request.client.host if request.client else "unknown"
    request_id = id(request)

    try:
        # Get user info and tokens from the dependency
        user = auth_data["user"]
        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")
        user_id = user.user.id

        logger.info(
            f"[Request {request_id}] Getting readings for user: {user.user.email} (ID: {user_id}) from {client_host}"
        )
        logger.info(
            f"[Request {request_id}] Access token provided: {access_token is not None}"
        )
        logger.info(
            f"[Request {request_id}] Refresh token provided: {refresh_token is not None}"
        )

        # Create authenticated client with both tokens when available
        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)

        # Query with the authenticated client
        logger.info(f"[Request {request_id}] Executing query on user_readings table")
        start_time = time.time()
        response = supabase.table("user_readings").select("*").execute()
        query_time = time.time() - start_time

        result_count = len(response.data) if response.data else 0
        logger.info(
            f"[Request {request_id}] Query completed in {query_time:.2f}s, returned {result_count} readings"
        )

        # If no results with RLS, try with explicit filter
        if not response.data:
            logger.info(
                f"[Request {request_id}] No results with RLS, trying with explicit user_id filter"
            )
            start_time = time.time()
            response = (
                supabase.table("user_readings")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            filter_query_time = time.time() - start_time
            filter_result_count = len(response.data) if response.data else 0

            logger.info(
                f"[Request {request_id}] Explicit filter query completed in {filter_query_time:.2f}s, returned {filter_result_count} readings"
            )

        return response.data if response.data else []

    except Exception as e:
        logger.error(f"[Request {request_id}] Error in get_user_readings: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/readings")
async def save_reading(
    request: Request, reading_data: Dict[str, Any], auth_data=Depends(verify_jwt)
):
    """
    Save a new reading for the authenticated user.
    """
    client_host = request.client.host if request.client else "unknown"
    request_id = id(request)

    try:
        # Get user info and tokens from the dependency
        user = auth_data["user"]
        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")
        user_id = user.user.id

        logger.info(
            f"[Request {request_id}] Saving reading for user: {user.user.email} (ID: {user_id}) from {client_host}"
        )

        # Log important reading data (excluding the full prediction which could be large)
        if "question" in reading_data:
            logger.info(
                f"[Request {request_id}] Question: {reading_data.get('question')}"
            )

        logger.debug(
            f"[Request {request_id}] Numbers: {reading_data.get('first_number')}, {reading_data.get('second_number')}, {reading_data.get('third_number')}"
        )

        # Create authenticated client with both tokens when available
        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)

        # Ensure user_id is set
        reading_data["user_id"] = user_id
        logger.debug(f"[Request {request_id}] Set user_id in reading data to {user_id}")

        # Insert the reading
        logger.info(f"[Request {request_id}] Inserting new reading record")
        start_time = time.time()
        response = supabase.table("user_readings").insert(reading_data).execute()
        insert_time = time.time() - start_time

        success = response.data is not None
        logger.info(
            f"[Request {request_id}] Insert completed in {insert_time:.2f}s, success: {success}"
        )

        return {"success": True, "data": response.data}

    except Exception as e:
        logger.error(f"[Request {request_id}] Error in save_reading: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
