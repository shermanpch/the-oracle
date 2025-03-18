"""
Data models for the Oracle I Ching API.

This module contains Pydantic models that define the structure of requests and responses
in the API, ensuring proper data validation and documentation.
"""

from pydantic import BaseModel

from src.app.core.output import IChingOutput


class OracleRequest(BaseModel):
    """Request model for the Oracle API."""

    question: str
    first_number: int
    second_number: int
    third_number: int
    language: str = "English"


class OracleResponse(IChingOutput):
    """Response model for the Oracle API, inheriting from IChingOutput."""

    pass


class UpdateReadingRequest(BaseModel):
    """Request model for updating a reading with clarifying questions and answers."""

    reading_id: str
    clarifying_question: str
    clarifying_answer: str


class FollowUpRequest(BaseModel):
    """Request model for follow-up questions about previous readings."""

    question: str
    conversation_history: list[dict[str, str]]


class UpdateUserQuotaRequest(BaseModel):
    """
    Request model for updating user quota information.
    """

    membership_type: str  # "free" or "premium"
