from datetime import datetime, timedelta, timezone

from app.services.supabase_client import supabase

MAX_POSTS_PER_HOUR = 5


def check_rate_limit(account_id: str) -> bool:
    """Returns True if within rate limit, False if exceeded.

    DB-backed: counts events posted by this account in the last hour,
    so the limit persists across server restarts.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    result = (
        supabase.table("events")
        .select("event_id", count="exact")
        .eq("fk_account_id", account_id)
        .gte("created_at", cutoff)
        .execute()
    )
    return (result.count or 0) < MAX_POSTS_PER_HOUR
