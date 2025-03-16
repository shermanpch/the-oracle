from typing import Any

from pydantic import BaseModel


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
