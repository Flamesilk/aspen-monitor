from contextlib import asynccontextmanager
from fastapi import FastAPI
import config
from telegram.ext import Application, JobQueue
from typing import AsyncGenerator
from bot.handlers import setup_commands

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Handling-network-errors
ptb = (
    Application.builder()
    .token(config.TELEGRAM_TOKEN)
    .read_timeout(7)
    .get_updates_read_timeout(42)
    .job_queue(JobQueue())  # Create a new JobQueue instance
)
if config.ENV:
    ptb = ptb.updater(None)
ptb = ptb.build()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    await setup_commands(ptb)
    if config.WEBHOOK_URL:
        await ptb.bot.set_webhook(
            url=f"{config.WEBHOOK_URL}",
            allowed_updates=['message', 'callback_query']
        )
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()
