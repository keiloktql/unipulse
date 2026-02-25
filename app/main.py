import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update

from app.bot import create_application
from app.config import settings
from app.services.supabase_client import supabase, verify_access_token

logger = logging.getLogger(__name__)

ptb_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ptb_app
    try:
        ptb_app = create_application()
        await ptb_app.initialize()
        await ptb_app.start()
        await ptb_app.bot.set_webhook(
            url=f"{settings.WEBHOOK_URL}/webhook",
            secret_token=settings.WEBHOOK_SECRET,
        )
        # Start background scheduler for reminders and newsletters
        from app.services.scheduler import init_scheduler, shutdown_scheduler
        init_scheduler(ptb_app.bot)
        logger.info("Startup complete")
    except Exception:
        logger.exception("Startup failed")
    yield
    if ptb_app:
        from app.services.scheduler import shutdown_scheduler
        shutdown_scheduler()
        await ptb_app.stop()
        await ptb_app.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.WEBHOOK_SECRET:
        return Response(status_code=403)
    data = await request.json()
    update = Update.de_json(data=data, bot=ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@app.get("/auth/callback")
async def auth_callback():
    """Supabase magic link redirects here with tokens in the URL fragment."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head><title>UniPulse Verification</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px">
<h2>Verifying your account...</h2>
<p id="status">Please wait.</p>
<script>
const hash = window.location.hash.substring(1);
const params = new URLSearchParams(hash);
const accessToken = params.get('access_token');
if (accessToken) {
    fetch('/auth/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({access_token: accessToken})
    })
    .then(r => r.json())
    .then(data => {
        document.querySelector('h2').textContent = data.ok ? 'Verified!' : 'Verification failed';
        document.getElementById('status').textContent = data.message;
    })
    .catch(() => {
        document.querySelector('h2').textContent = 'Error';
        document.getElementById('status').textContent = 'Something went wrong. Please try /verify again.';
    });
} else {
    document.querySelector('h2').textContent = 'Error';
    document.getElementById('status').textContent = 'No token found. Please try /verify again.';
}
</script>
</body>
</html>""")


@app.post("/auth/complete")
async def auth_complete(request: Request):
    """Verify access token, create account, notify user via Telegram."""
    data = await request.json()
    access_token = data.get("access_token")
    if not access_token:
        return JSONResponse({"ok": False, "message": "Missing token."})

    # Verify token with Supabase Auth
    try:
        auth_user = verify_access_token(access_token)
    except Exception:
        return JSONResponse({"ok": False, "message": "Invalid or expired token. Please try /verify again."})

    if not auth_user or not auth_user.email:
        return JSONResponse({"ok": False, "message": "Could not verify email. Please try /verify again."})

    # Look up pending verification
    from app.handlers.verify import pending_verifications

    email = auth_user.email.lower()
    pending = pending_verifications.pop(email, None)
    if not pending:
        return JSONResponse({"ok": False, "message": "No pending verification for this email. Please run /verify first."})

    telegram_id = pending["telegram_id"]
    tele_handle = pending["tele_handle"]

    # Create/update account
    try:
        supabase.table("accounts").upsert({
            "account_id": str(auth_user.id),
            "telegram_id": telegram_id,
            "tele_handle": tele_handle,
            "is_verified": True,
            "auth_user_id": str(auth_user.id),
        }, on_conflict="account_id").execute()
        logger.info("User verified: @%s (%s)", tele_handle, email)
    except Exception as e:
        logger.error("Failed to save account: %s", e)
        return JSONResponse({"ok": False, "message": "Verification succeeded but failed to save. Please contact support."})

    # Send confirmation via Telegram
    if ptb_app:
        try:
            await ptb_app.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "You're verified!\n\n"
                    "You now have full access to UniPulse.\n"
                    "Use /events to browse, /subscribe to follow categories,\n"
                    "and post events in group chats with #unipulse."
                ),
            )
        except Exception as e:
            logger.error("Failed to send verification confirmation to %s: %s", telegram_id, e)

    return JSONResponse({"ok": True, "message": "You're verified! You can close this tab and return to Telegram."})


@app.get("/health")
async def health():
    return {"status": "ok"}
