import uuid
from datetime import datetime, timezone
from typing import List, Optional

from supabase import create_client, Client

from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)


# --- Auth ---

def send_verification_email(email: str, redirect_url: str, tele_id: int, tele_handle: str):
    """Send a confirmation email for NUS identity verification.

    Stores tele_id and tele_handle in Supabase Auth user metadata so they
    are available when the confirmation link is clicked — no separate pending table needed.
    """
    supabase.auth.sign_up({
        "email": email,
        "password": str(uuid.uuid4()),
        "options": {
            "email_redirect_to": redirect_url,
            "data": {
                "tele_id": tele_id,
                "tele_handle": tele_handle,
            },
        },
    })


def verify_access_token(access_token: str):
    """Verify an access token and return the auth user."""
    return supabase.auth.get_user(access_token).user


# --- Events ---

def get_event(event_id: str) -> Optional[dict]:
    result = supabase.table("events").select("*").eq("event_id", event_id).maybe_single().execute()
    return result.data


def get_event_by_hash(text_hash: str) -> Optional[dict]:
    result = supabase.table("events").select("event_id").eq("text_hash", text_hash).maybe_single().execute()
    return result.data


def save_event(
    text: str,
    date: Optional[str] = None,
    account_id: Optional[str] = None,
    title: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    end_date: Optional[str] = None,
    text_hash: Optional[str] = None,
) -> dict:
    data = {"text": text, "fk_account_id": account_id}
    if date:
        data["date"] = date
    if title:
        data["title"] = title
    if location:
        data["location"] = location
    if description:
        data["description"] = description
    if end_date:
        data["end_date"] = end_date
    if text_hash:
        data["text_hash"] = text_hash
    result = supabase.table("events").insert(data).execute()
    return result.data[0]


def update_event_refs(event_id: str, ec_id: Optional[str] = None, ei_id: Optional[str] = None):
    data = {}
    if ec_id:
        data["fk_ec_id"] = ec_id
    if ei_id:
        data["fk_ei_id"] = ei_id
    if data:
        supabase.table("events").update(data).eq("event_id", event_id).execute()


# --- Categories ---

def get_or_create_category(name: str) -> dict:
    result = supabase.table("categories").select("*").eq("name", name).maybe_single().execute()
    if result.data:
        return result.data
    result = supabase.table("categories").insert({"name": name}).execute()
    return result.data[0]


def link_event_category(event_id: str, category_id: str) -> dict:
    result = supabase.table("event_categories").insert({
        "fk_event_id": event_id,
        "fk_category_id": category_id,
    }).execute()
    return result.data[0]


# --- Images ---

def upload_image(image_bytes: bytes, extension: str = "jpg") -> str:
    filename = f"{uuid.uuid4()}.{extension}"
    supabase.storage.from_("event-posters").upload(
        filename, image_bytes, {"content-type": f"image/{extension}"}
    )
    return f"{settings.SUPABASE_URL}/storage/v1/object/public/event-posters/{filename}"


def save_event_image(event_id: str, url: str) -> dict:
    result = supabase.table("event_images").insert({
        "fk_event_id": event_id,
        "url": url,
    }).execute()
    return result.data[0]


# --- RSVPs ---

def upsert_rsvp(event_id: str, account_id: str) -> int:
    """Toggle RSVP for this user+event. Returns updated total RSVP count."""
    result = supabase.rpc("upsert_rsvp", {
        "p_event_id": event_id,
        "p_account_id": account_id,
    }).execute()
    return result.data or 0


def get_rsvp_counts(event_id: str) -> int:
    """Return total RSVP count for an event."""
    result = (
        supabase.table("rsvps")
        .select("rsvp_id", count="exact")
        .eq("fk_event_id", event_id)
        .execute()
    )
    return result.count or 0


# --- Admins ---

def is_verified_admin(tele_handle: str) -> bool:
    """A user is verified if they have an account record (account_id FK'd to auth.users)."""
    result = (
        supabase.table("accounts")
        .select("account_id")
        .eq("tele_handle", tele_handle)
        .maybe_single()
        .execute()
    )
    return result.data is not None


def is_verified_admin_by_tele_id(tele_id: int) -> bool:
    """A user is verified if they have an account record (account_id FK'd to auth.users)."""
    result = (
        supabase.table("accounts")
        .select("account_id")
        .eq("tele_id", tele_id)
        .maybe_single()
        .execute()
    )
    return result.data is not None


def get_account_by_handle(tele_handle: str) -> Optional[dict]:
    result = supabase.table("accounts").select("*").eq("tele_handle", tele_handle).maybe_single().execute()
    return result.data


def get_account_by_tele_id(tele_id: int) -> Optional[dict]:
    result = supabase.table("accounts").select("*").eq("tele_id", tele_id).maybe_single().execute()
    return result.data


# --- Browse ---

def get_all_events(limit: int = 10) -> List[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    result = (
        supabase.table("events")
        .select("*")
        .eq("is_deleted", False)
        .gte("date", now_iso)
        .order("date", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data


def get_trending_events(limit: int = 5) -> List[dict]:
    """Get events sorted by most RSVPs (going + interested)."""
    result = (
        supabase.table("rsvps")
        .select("fk_event_id, events(*)")
        .execute()
    )
    now = datetime.now(timezone.utc)
    event_counts = {}
    event_data = {}
    for row in result.data:
        eid = row["fk_event_id"]
        event = row.get("events")
        if not event:
            continue
        # Skip deleted events
        if event.get("is_deleted"):
            continue
        # Skip past events
        if event.get("date"):
            try:
                event_dt = datetime.fromisoformat(event["date"])
                if event_dt < now:
                    continue
            except (ValueError, TypeError):
                pass
        event_counts[eid] = event_counts.get(eid, 0) + 1
        if eid not in event_data:
            event_data[eid] = event

    sorted_ids = sorted(event_counts, key=event_counts.get, reverse=True)[:limit]
    return [event_data[eid] for eid in sorted_ids if eid in event_data]


# --- Search ---

def search_events(query: Optional[str] = None, category: Optional[str] = None, limit: int = 10) -> List[dict]:
    result = supabase.rpc("search_events", {
        "p_query": query,
        "p_category": category,
        "p_limit": limit,
    }).execute()
    return result.data


# --- Event editing ---

def update_event(event_id: str, **fields) -> dict:
    """Update specific fields on an event."""
    result = supabase.table("events").update(fields).eq("event_id", event_id).execute()
    return result.data[0]


def get_events_by_account(account_id: str, limit: int = 10) -> List[dict]:
    """Get all events (including deleted) posted by this account, newest first."""
    result = (
        supabase.table("events")
        .select("*")
        .eq("fk_account_id", account_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


