"""
API routes for the Oracle I Ching API.

This module contains all the API route definitions and handlers for the Oracle I Ching API.
"""

import logging
import time
import traceback
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from src.app.api.models import (
    FollowUpRequest,
    OracleRequest,
    OracleResponse,
    UpdateReadingRequest,
    UpdateUserQuotaRequest,
)
from src.app.core.oracle import Oracle
from src.config.quotas import FREE_PLAN_QUOTA, PREMIUM_PLAN_QUOTA
from src.utils.llm_handler import get_follow_up_from_llm, get_reading_from_llm
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

        return {
            "user": user,
            "access_token": access_token,
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
            f"[Request {request_id}] Fetching parent text for coordinates {oracle.get_parent_directory()}"
        )
        parent_content = oracle.get_parent_text()

        logger.debug(
            f"[Request {request_id}] Fetching child text for coordinates {oracle.get_parent_directory()}/{oracle.get_child_directory()}"
        )
        child_content = oracle.get_child_text()

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
        result = get_reading_from_llm(
            oracle_request.question,
            parent_content,
            child_content,
            oracle_request.language,
            "env",
        )
        llm_time = time.time() - start_time
        logger.info(f"[Request {request_id}] LLM response received in {llm_time:.2f}s")

        result.image_path = child_image_path

        # Convert the Pydantic model to a dictionary
        response_dict = result.model_dump()

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

        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)
        logger.info(f"[Request {request_id}] Executing query on user_readings table")
        start_time = time.time()
        response = supabase.table("user_readings").select("*").execute()
        query_time = time.time() - start_time

        result_count = len(response.data) if response.data else 0
        logger.info(
            f"[Request {request_id}] Query completed in {query_time:.2f}s, returned {result_count} readings"
        )

        return response.data if response.data else []

    except Exception as e:
        logger.error(f"[Request {request_id}] Error in get_user_readings: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/readings/{reading_id}", response_model=Dict[str, Any])
async def get_reading_by_id(
    reading_id: str, request: Request, auth_data=Depends(verify_jwt)
):
    """
    Get a specific reading by ID for the authenticated user.

    Args:
        reading_id: The ID of the reading to retrieve
        request: The FastAPI request object
        auth_data: Authentication data from the verify_jwt dependency

    Returns:
        The reading data if found, or a 404 error if not found
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
            f"[Request {request_id}] Getting reading ID {reading_id} for user: {user.user.email} (ID: {user_id}) from {client_host}"
        )

        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)

        logger.info(
            f"[Request {request_id}] Executing query for reading ID {reading_id}"
        )
        start_time = time.time()

        # Query the specific reading by ID and ensure it belongs to the authenticated user
        response = (
            supabase.table("user_readings")
            .select("*")
            .eq("id", reading_id)
            .eq("user_id", user_id)
            .execute()
        )

        query_time = time.time() - start_time
        logger.info(f"[Request {request_id}] Query completed in {query_time:.2f}s")

        # Check if the reading exists
        if not response.data or len(response.data) == 0:
            logger.warning(
                f"[Request {request_id}] Reading ID {reading_id} not found for user {user_id}"
            )
            raise HTTPException(status_code=404, detail="Reading not found")

        logger.info(
            f"[Request {request_id}] Successfully retrieved reading ID {reading_id}"
        )
        return response.data[0]

    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.error(f"[Request {request_id}] Error in get_reading_by_id: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/readings")
async def save_user_reading(
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

        if "question" in reading_data:
            logger.info(
                f"[Request {request_id}] Question: {reading_data.get('question')}"
            )

        logger.debug(
            f"[Request {request_id}] Numbers: {reading_data.get('first_number')}, {reading_data.get('second_number')}, {reading_data.get('third_number')}"
        )

        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)

        reading_data["user_id"] = user_id
        logger.debug(f"[Request {request_id}] Set user_id in reading data to {user_id}")

        logger.info(f"[Request {request_id}] Inserting new reading record")
        start_time = time.time()
        response = supabase.table("user_readings").insert(reading_data).execute()
        end_time = time.time() - start_time

        success = response.data is not None
        logger.info(
            f"[Request {request_id}] Insert completed in {end_time:.2f}s, success: {success}"
        )

        return {"success": True, "data": response.data}

    except Exception as e:
        logger.error(f"[Request {request_id}] Error in save_reading: {str(e)}")
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oracle/followup")
async def get_follow_up_response(
    request: Request, follow_up_request: FollowUpRequest, auth_data=Depends(verify_jwt)
):
    """
    Get a follow-up response to a clarifying question about a previous I Ching reading.
    Requires authentication.
    """
    client_host = request.client.host if request.client else "unknown"
    request_id = id(request)

    try:
        # Get user info and tokens from the dependency
        user = auth_data["user"]
        user_id = user.user.id
        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")

        logger.info(
            f"[Request {request_id}] Processing follow-up question for user: {user.user.email} from {client_host}"
        )
        logger.info(f"[Request {request_id}] Question: {follow_up_request.question}")

        logger.info(f"[Request {request_id}] Querying LLM for follow-up response")
        start_time = time.time()
        response_text = get_follow_up_from_llm(
            follow_up_request.conversation_history,
            follow_up_request.question,
            "env",
        )
        end_time = time.time() - start_time

        logger.info(f"[Request {request_id}] LLM response received in {end_time:.2f}s")

        return {"response": response_text, "success": True}

    except Exception as e:
        logger.error(
            f"[Request {request_id}] Error in get_follow_up_response: {str(e)}"
        )
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/readings/update")
async def update_reading_clarification(
    request: Request, update_data: UpdateReadingRequest, auth_data=Depends(verify_jwt)
):
    """
    Update a reading with clarifying question and answer.
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
            f"[Request {request_id}] Updating reading with clarification for user: {user.user.email} (ID: {user_id}) from {client_host}"
        )
        logger.info(f"[Request {request_id}] Reading ID: {update_data.reading_id}")
        logger.info(
            f"[Request {request_id}] Clarifying Question: {update_data.clarifying_question}"
        )

        # Create authenticated client with both tokens when available
        logger.debug(f"[Request {request_id}] Creating authenticated Supabase client")
        supabase = get_supabase_client(access_token, refresh_token)

        # Update the reading
        logger.info(f"[Request {request_id}] Updating reading record")
        start_time = time.time()
        response = (
            supabase.table("user_readings")
            .update(
                {
                    "clarifying_question": update_data.clarifying_question,
                    "clarifying_answer": update_data.clarifying_answer,
                }
            )
            .eq("id", update_data.reading_id)
            .execute()
        )
        end_time = time.time() - start_time

        success = response.data is not None
        logger.info(
            f"[Request {request_id}] Update completed in {end_time:.2f}s, success: {success}"
        )

        return {"success": True, "data": response.data}

    except Exception as e:
        logger.error(
            f"[Request {request_id}] Error in update_reading_clarification: {str(e)}"
        )
        logger.debug(f"[Request {request_id}] Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/quota")
async def get_user_quota(request: Request, auth_data=Depends(verify_jwt)):
    """
    Get user quota information.

    Returns current quota status including membership type, remaining queries,
    and the maximum queries for their current membership level.
    """
    user = auth_data["user"]
    user_id = user.user.id

    logger.info(f"Getting quota for user: {user.user.email} (ID: {user_id})")

    supabase = get_supabase_client(
        auth_data.get("access_token"), auth_data.get("refresh_token")
    )

    # Check if user quota exists
    result = supabase.table("user_quotas").select("*").eq("user_id", user_id).execute()

    # If no quota record exists, create one with default values
    if not result.data:
        logger.info(
            f"No quota record found for user {user_id}. Creating default quota."
        )
        # Default to free membership with configured quota
        new_quota = {
            "user_id": user_id,
            "membership_type": "free",
            "remaining_queries": FREE_PLAN_QUOTA,
        }
        supabase.table("user_quotas").insert(new_quota).execute()

        # Add max_queries field to response
        response = new_quota.copy()
        response["max_queries"] = FREE_PLAN_QUOTA
        return response

    # Add max_queries field based on membership type
    response = result.data[0]
    membership_type = response.get("membership_type", "free")
    max_queries = (
        PREMIUM_PLAN_QUOTA if membership_type == "premium" else FREE_PLAN_QUOTA
    )
    response["max_queries"] = max_queries

    logger.info(
        f"Quota for user {user_id}: {response['remaining_queries']} of {max_queries} queries ({membership_type})"
    )

    return response


@router.post("/user/quota/decrement")
async def decrement_user_quota(request: Request, auth_data=Depends(verify_jwt)):
    """
    Decrement user's remaining queries.

    This reduces the user's available queries by 1 if they have queries remaining.
    """
    user = auth_data["user"]
    user_id = user.user.id

    logger.info(f"Decrementing quota for user: {user.user.email} (ID: {user_id})")

    supabase = get_supabase_client(
        auth_data.get("access_token"), auth_data.get("refresh_token")
    )

    # Get current quota
    result = supabase.table("user_quotas").select("*").eq("user_id", user_id).execute()

    if not result.data:
        # If no record exists, create one with default free quota
        logger.info(
            f"No quota record found for user {user_id}. Creating default quota."
        )
        new_quota = {
            "user_id": user_id,
            "membership_type": "free",
            "remaining_queries": FREE_PLAN_QUOTA,
        }
        supabase.table("user_quotas").insert(new_quota).execute()
        return {"remaining_queries": FREE_PLAN_QUOTA}

    # If quota exists, decrement if greater than 0
    current_quota = result.data[0]

    # Get current values
    membership_type = current_quota["membership_type"]
    remaining = current_quota["remaining_queries"]

    logger.info(f"Current quota for user {user_id}: {remaining} queries remaining")

    if remaining > 0:
        # Simple decrement, no conditional logic here
        updated_remaining = remaining - 1
        logger.info(f"Decrementing quota for user {user_id} to {updated_remaining}")

        updated = (
            supabase.table("user_quotas")
            .update({"remaining_queries": updated_remaining})
            .eq("user_id", user_id)
            .execute()
        )

        return {"remaining_queries": updated_remaining}

    # If no queries remaining, return current value
    logger.info(f"User {user_id} has no queries remaining")
    return {"remaining_queries": 0}


@router.post("/user/quota/update", response_model=Dict)
def update_user_quota(
    request: Request,
    user_quota: UpdateUserQuotaRequest,
    auth_data=Depends(verify_jwt),
):
    """
    Update a user's quota information.

    When a user upgrades from free to premium, their remaining queries are set to
    the premium quota amount defined in the configuration.
    """
    try:
        # Get the user ID from the token
        user = auth_data["user"]
        user_id = user.user.id
        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")

        logger.info(f"Updating quota for user: {user.user.email} (ID: {user_id})")

        # Update the user's quota
        membership_type = user_quota.membership_type
        logger.info(f"Changing membership type to: {membership_type}")

        # Get the current quota
        supabase = get_supabase_client(access_token, refresh_token)
        result = (
            supabase.table("user_quotas").select("*").eq("user_id", user_id).execute()
        )

        if not result.data:
            logger.error(f"User quota not found for user ID: {user_id}")
            return {"error": "User quota not found"}

        current_quota = result.data[0]
        current_membership = current_quota["membership_type"]

        updated_quota = {
            "membership_type": membership_type,
        }

        # If upgrading to premium, reset queries to premium amount
        if current_membership != "premium" and membership_type == "premium":
            logger.info(
                f"User upgrading from {current_membership} to premium. Resetting quota to {PREMIUM_PLAN_QUOTA}"
            )
            updated_quota["remaining_queries"] = PREMIUM_PLAN_QUOTA

        logger.info(f"Updating user quota in database: {updated_quota}")
        updated = (
            supabase.table("user_quotas")
            .update(updated_quota)
            .eq("user_id", user_id)
            .execute()
        )

        return {"status": "success", "data": updated.data}
    except Exception as e:
        logger.error(f"Error updating user quota: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user quota: {str(e)}",
        )
