import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-3-flash-preview"

TEXT_EXTRACTION_PROMPT = """Extract event details from the following message text.
Return a JSON object with these fields:
- title: string (short event title, or null if not determinable)
- date: string (ISO 8601 start datetime e.g. "2026-03-01T19:00:00+08:00", or null)
- end_date: string (ISO 8601 end datetime, or null if not found)
- location: string (event location/venue, or null if not found)
- description: string (brief event description, or null)

Only return valid JSON. Use null for fields that cannot be determined."""

IMAGE_EXTRACTION_PROMPT = """I could not find event details from the message text.

Please look at the attached event poster/image and extract:
Return a JSON object with these fields:
- title: string (short event title, or null if not determinable)
- date: string (ISO 8601 start datetime e.g. "2026-03-01T19:00:00+08:00", or null)
- end_date: string (ISO 8601 end datetime, or null if not found)
- location: string (event location/venue, or null if not found)
- description: string (brief event description, or null)

Only return valid JSON. Use null for fields that cannot be determined."""


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
        return {"date": None, "title": None, "end_date": None, "location": None, "description": None}


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
        return {"date": None, "title": None, "end_date": None, "location": None, "description": None}


def parse_event(text: str, image_bytes: Optional[bytes] = None) -> dict:
    """Extract event details: text first, image fallback for missing fields."""
    result = parse_text(text)

    if image_bytes:
        # If date is missing from text, try image
        if result.get("date") is None:
            logger.info("Date not found in text, falling back to image parsing")
            image_result = parse_image(image_bytes)
            # Fill in missing fields from image result
            for key in ("date", "title", "end_date", "location", "description"):
                if result.get(key) is None and image_result.get(key) is not None:
                    result[key] = image_result[key]

    return result
