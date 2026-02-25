-- UniPulse migrations
-- Run this in the Supabase SQL editor


-- Ensure events table has created_at column for persistent rate limiting
ALTER TABLE events ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();


-- RPC function: atomic RSVP toggle, returns updated total count for this event
CREATE OR REPLACE FUNCTION upsert_rsvp(
  p_event_id uuid,
  p_account_id uuid
)
RETURNS int AS $$
DECLARE
  existing_id uuid;
  new_count int;
BEGIN
  SELECT rsvp_id INTO existing_id
  FROM rsvps WHERE fk_event_id = p_event_id AND fk_account_id = p_account_id;

  IF existing_id IS NOT NULL THEN
    DELETE FROM rsvps WHERE rsvp_id = existing_id;
  ELSE
    INSERT INTO rsvps (fk_event_id, fk_account_id)
    VALUES (p_event_id, p_account_id);
  END IF;

  SELECT count(*)::int INTO new_count FROM rsvps WHERE fk_event_id = p_event_id;
  RETURN new_count;
END;
$$ LANGUAGE plpgsql;
