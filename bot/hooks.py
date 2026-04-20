from collections.abc import Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes

HookFn = Callable[[Update, ContextTypes.DEFAULT_TYPE, str], Awaitable[None]]


async def hook_ping(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
    await update.effective_message.reply_text("pong")


async def hook_echo(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
    text = payload.strip() or "(empty)"
    await update.effective_message.reply_text(text)


async def hook_health(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
    me = await context.bot.get_me()
    await update.effective_message.reply_text(f"ok: @{me.username or me.id}")


def register_hooks() -> dict[str, HookFn]:
    return {
        "ping": hook_ping,
        "echo": hook_echo,
        "health": hook_health,
    }

