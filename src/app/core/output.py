from typing import Any, Dict, Optional

from pydantic import BaseModel


# These models are kept for reference but not used directly in IChingOutput anymore
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
    Represents a hexagram in the I Ching, including its name, meaning, and advice.
    """

    hexagram_name: str
    summary: str
    interpretation: str
    line_change: LineChange
    result: HexagramResult
    advice: str
    image_path: Optional[str] = None
