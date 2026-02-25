from datetime import datetime, timedelta
from urllib.parse import quote


def build_gcal_url(event: dict) -> str | None:
    """Generate Google Calendar deep link from event data."""
    date = event.get("date")
    if not date:
        return None

    title = event.get("title") or event.get("text", "")[:50]
    location = event.get("location") or ""
    description = event.get("description") or event.get("text", "")[:200]

    try:
        start_dt = datetime.fromisoformat(date)
    except (ValueError, TypeError):
        return None

    start_str = start_dt.strftime("%Y%m%dT%H%M%S")

    end_date = event.get("end_date")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except (ValueError, TypeError):
            end_dt = start_dt + timedelta(hours=2)
    else:
        end_dt = start_dt + timedelta(hours=2)
    end_str = end_dt.strftime("%Y%m%dT%H%M%S")

    dates = f"{start_str}/{end_str}"

    url = (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={dates}"
        f"&details={quote(description)}"
        f"&location={quote(location)}"
    )
    return url
