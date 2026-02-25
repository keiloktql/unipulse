-- UniPulse: New table for Pulse Count
-- Run this in the Supabase SQL editor


-- RPC function: atomic RSVP upsert, returns current counts from rsvps table
CREATE OR REPLACE FUNCTION upsert_rsvp(
  p_event_id uuid,
  p_account_id uuid,
  p_status text
)
RETURNS TABLE(new_going_count int, new_interested_count int) AS $$
DECLARE
  old_status text;
BEGIN
  SELECT status INTO old_status
  FROM rsvps WHERE fk_event_id = p_event_id AND fk_account_id = p_account_id;

  IF old_status IS NOT NULL THEN
    IF old_status = p_status THEN
      DELETE FROM rsvps WHERE fk_event_id = p_event_id AND fk_account_id = p_account_id;
    ELSE
      UPDATE rsvps SET status = p_status
      WHERE fk_event_id = p_event_id AND fk_account_id = p_account_id;
    END IF;
  ELSE
    INSERT INTO rsvps (fk_event_id, fk_account_id, status)
    VALUES (p_event_id, p_account_id, p_status);
  END IF;

  RETURN QUERY SELECT
    (SELECT count(*)::int FROM rsvps WHERE fk_event_id = p_event_id AND status = 'going'),
    (SELECT count(*)::int FROM rsvps WHERE fk_event_id = p_event_id AND status = 'interested');
END;
$$ LANGUAGE plpgsql;
