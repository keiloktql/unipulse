import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update

from app.bot import create_application
from app.config import settings
from app.services.scheduler import init_scheduler, shutdown_scheduler

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
        init_scheduler(ptb_app.bot)
        logger.info("Startup complete")
    except Exception:
        logger.exception("Startup failed")
    yield
    if ptb_app:
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


@app.get("/health")
async def health():
    return {"status": "ok"}
