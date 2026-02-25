import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-3-flash-preview"

TEXT_EXTRACTION_PROMPT = """Extract the event date/time from the following message text.
Return a JSON object with this field:
- date: string (ISO 8601 datetime e.g. "2026-03-01T19:00:00+08:00", or null if not found)

Only return valid JSON. If the date cannot be determined from the text, use null."""

IMAGE_EXTRACTION_PROMPT = """I could not find the event date/time from the message text.

Please look at the attached event poster/image and extract the date/time.
Return a JSON object with this field:
- date: string (ISO 8601 datetime e.g. "2026-03-01T19:00:00+08:00", or null if not found)

Only return valid JSON. If the date cannot be determined, use null."""


def parse_text(text: str) -> dict:
    response = client.models.generate_content(
        model=MODEL,
        contents=text + "\n\n" + TEXT_EXTRACTION_PROMPT,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, ValueError):
        logger.error("Failed to parse Gemini text response: %s", response.text)
        return {"date": None}


def parse_image(image_bytes: bytes) -> dict:
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            IMAGE_EXTRACTION_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, ValueError):
        logger.error("Failed to parse Gemini image response: %s", response.text)
        return {"date": None}


def parse_event(text: str, image_bytes: Optional[bytes] = None) -> dict:
    """Extract event date: text first, image fallback if date is missing."""
    result = parse_text(text)

    if result.get("date") is None and image_bytes:
        logger.info("Date not found in text, falling back to image parsing")
        result = parse_image(image_bytes)

    return result
