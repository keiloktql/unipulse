from typing import Optional

from pydantic import BaseModel


class ParsedEvent(BaseModel):
    date: Optional[str] = None
