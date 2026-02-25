from typing import List, Optional

from app.services.supabase_client import supabase

# Message shown when unverified user tries to use a feature
VERIFY_MSG = "🔒 You need to verify your NUS identity first.\nDM me with /verify to get started."


def get_verified_account(telegram_id: int) -> Optional[dict]:
    """Return account for this telegram_id, or None if not found.

    Having an account record means the user has completed NUS email verification
    (account_id is FK'd to auth.users, so it can only exist post-verification).
    """
    result = (
        supabase.table("accounts")
        .select("*")
        .eq("telegram_id", telegram_id)
        .maybe_single()
        .execute()
    )
    return result.data


def get_all_categories() -> List[dict]:
    result = supabase.table("categories").select("*").order("name").execute()
    return result.data


def get_account_subscriptions(account_id: str) -> List[dict]:
    result = (
        supabase.table("account_categories")
        .select("fk_category_id")
        .eq("fk_account_id", account_id)
        .execute()
    )
    return result.data


def get_category_subscriber_counts() -> dict:
    """Return {category_id: subscriber_count} for all categories."""
    result = supabase.table("account_categories").select("fk_category_id").execute()
    counts: dict[str, int] = {}
    for row in result.data:
        cid = row["fk_category_id"]
        counts[cid] = counts.get(cid, 0) + 1
    return counts


def toggle_subscription(account_id: str, category_id: str) -> bool:
    """Toggle subscription. Returns True if subscribed, False if unsubscribed."""
    existing = (
        supabase.table("account_categories")
        .select("ac_id")
        .eq("fk_account_id", account_id)
        .eq("fk_category_id", category_id)
        .maybe_single()
        .execute()
    )
    if existing.data:
        (
            supabase.table("account_categories")
            .delete()
            .eq("ac_id", existing.data["ac_id"])
            .execute()
        )
        return False
    (
        supabase.table("account_categories")
        .insert({"fk_account_id": account_id, "fk_category_id": category_id})
        .execute()
    )
    return True


def update_newsletter_time(account_id: str, time_str: str):
    (
        supabase.table("accounts")
        .update({"newsletter_time": time_str})
        .eq("account_id", account_id)
        .execute()
    )
