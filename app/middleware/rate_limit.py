from collections import defaultdict
from datetime import datetime, timedelta

_post_timestamps: dict[int, list[datetime]] = defaultdict(list)
MAX_POSTS_PER_HOUR = 5


def check_rate_limit(telegram_id: int) -> bool:
    """Returns True if within rate limit, False if exceeded."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)
    _post_timestamps[telegram_id] = [t for t in _post_timestamps[telegram_id] if t > cutoff]
    if len(_post_timestamps[telegram_id]) >= MAX_POSTS_PER_HOUR:
        return False
    _post_timestamps[telegram_id].append(now)
    return True
