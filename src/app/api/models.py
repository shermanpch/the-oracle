"""
Data models for the Oracle I Ching API.

This module contains Pydantic models that define the structure of requests and responses
in the API, ensuring proper data validation and documentation.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class OracleRequest(BaseModel):
    """Request model for the Oracle API."""

    question: str
    first_number: int
    second_number: int
    third_number: int
    language: str = "English"


class HexagramResult(BaseModel):
    """Represents the resulting hexagram interpretation."""

    name: str
    interpretation: str


class LineChange(BaseModel):
    """Represents a specific changing line in the hexagram."""

    line: str
    interpretation: str


class IChingOutput(BaseModel):
    """
    Represents a hexagram in the I Ching, including its name, meaning, and investment advice.
    """

    hexagram_name: str
    summary: str
    interpretation: str
    line_change: LineChange
    result: HexagramResult
    advice: str


class OracleResponse(BaseModel):
    """Response model for the Oracle API."""

    hexagram_name: str
    summary: str
    interpretation: str
    line_change: Dict[str, Any]
    result: Dict[str, Any]
    advice: str
    image_path: Optional[str] = None
