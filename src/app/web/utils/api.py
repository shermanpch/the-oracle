"""
API utility functions for the Oracle application.

This module contains functions for making API requests to the Oracle backend.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Define API_URL at the module level so it's available to all functions
API_URL = os.getenv("API_URL", "https://oracle-api.onrender.com")


def make_api_request(endpoint, method="GET", payload=None, headers=None):
    """
    Make an API request and handle common error cases.

    Args:
        endpoint: API endpoint to call
        method: HTTP method (GET, POST, etc.)
        payload: Request payload for POST/PUT requests
        headers: Request headers

    Returns:
        Response data or None if error
    """
    try:
        if method.upper() == "GET":
            response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
        elif method.upper() == "POST":
            response = requests.post(
                f"{API_URL}/{endpoint}", json=payload, headers=headers
            )
        else:
            logger.error(f"Unsupported method: {method}")
            return None

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception in API request: {str(e)}")
        return None
