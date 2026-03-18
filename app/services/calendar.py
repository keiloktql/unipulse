from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))


def build_gcal_url(event: dict) -> str | None:
    """Generate Google Calendar deep link from event data."""
    date = event.get("date")
    if not date:
        return None

    title = event.get("title") or event.get("text", "")[:50]
    location = event.get("location") or ""
    description = event.get("description") or event.get("text", "")[:200]

    try:
        start_dt = datetime.fromisoformat(date).astimezone(SGT)
    except (ValueError, TypeError):
        return None

    # Google Calendar uses UTC format with Z suffix
    start_utc = start_dt.astimezone(timezone.utc)
    start_str = start_utc.strftime("%Y%m%dT%H%M%SZ")

    end_date = event.get("end_date")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date).astimezone(SGT)
        except (ValueError, TypeError):
            end_dt = start_dt + timedelta(hours=2)
    else:
        end_dt = start_dt + timedelta(hours=2)
    end_utc = end_dt.astimezone(timezone.utc)
    end_str = end_utc.strftime("%Y%m%dT%H%M%SZ")

    dates = f"{start_str}/{end_str}"

    url = (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={dates}"
        f"&details={quote(description)}"
        f"&location={quote(location)}"
        f"&ctz=Asia/Singapore"
    )
    return url
