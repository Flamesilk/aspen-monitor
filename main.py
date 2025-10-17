from http import HTTPStatus
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler
import uvicorn
from bot.ptb import ptb, lifespan
from bot.handlers import (start, fetch_grades, settings, status, donate, help_command,
                         admin_stats,
                         registration_handler, settings_handler, setup_handler, button_callback)
from bot.scheduler import setup_scheduler
import config
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with lifespan from ptb
app = FastAPI(lifespan=lifespan) if config.ENV else FastAPI()

# Add handlers
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("grades", fetch_grades))
ptb.add_handler(CommandHandler("settings", settings))
ptb.add_handler(CommandHandler("status", status))
ptb.add_handler(CommandHandler("donate", donate))
ptb.add_handler(CommandHandler("help", help_command))

# Admin handlers
ptb.add_handler(CommandHandler("admin", admin_stats))

# Add conversation handlers
ptb.add_handler(registration_handler)
ptb.add_handler(settings_handler)
ptb.add_handler(setup_handler)

# Add callback query handler
ptb.add_handler(CallbackQueryHandler(button_callback))

# Initialize scheduler
setup_scheduler(ptb)

# Use webhook when running in prod (via gunicorn)
if config.ENV:

    @app.post("/api/webhook")
    async def process_update(request: Request):
        try:
            req = await request.json()
            logger.info(f"Received update: {req}")
            update = Update.de_json(req, ptb.bot)

            # In serverless environment like Vercel, we need to initialize PTB for each request
            if config.SERVERLESS:
                async with ptb:
                    await ptb.process_update(update)
            else:
                await ptb.process_update(update)

            return Response(status_code=HTTPStatus.OK)
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}", exc_info=True)
            return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=str(e))

# Use polling when running locally
if __name__ == "__main__":
    if not config.ENV:
        logger.info("Running in local mode")
        ptb.run_polling()
    else:
        # Used for testing webhook locally, instructions for how to set up local webhook at https://dev.to/ibrarturi/how-to-test-webhooks-on-your-localhost-3b4f
        logger.info("Running in prod mode")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        # uvicorn.run(app, host="127.0.0.1", port=8000)
