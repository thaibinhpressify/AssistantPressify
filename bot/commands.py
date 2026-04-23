import asyncio
import json
import urllib.error
import urllib.request

from telegram import Update
from telegram.ext import ContextTypes

from .config import load_config
from .hooks import register_hooks


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Ready.\n\nCommands:\n/setup"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hooks = register_hooks()
    hook_names = ", ".join(sorted(hooks.keys()))
    await update.effective_message.reply_text(
        "Usage:\n"
        "/chatinfo\n"
        "/setup\n"
        "/hook list\n"
        "/hook <name> [payload]\n\n"
        f"Available hooks: {hook_names}"
    )


async def hook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hooks = register_hooks()
    args = context.args or []
    if not args:
        await help_cmd(update, context)
        return

    name = args[0].strip().lower()
    payload = " ".join(args[1:]).strip()

    if name in {"list", "ls"}:
        await update.effective_message.reply_text("\n".join(sorted(hooks.keys())))
        return

    hook_fn = hooks.get(name)
    if not hook_fn:
        await update.effective_message.reply_text(
            f"Unknown hook: {name}\n\nTry: /hook list"
        )
        return

    await hook_fn(update, context, payload)


async def chatinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat:
        return

    try:
        full_chat = await context.bot.get_chat(chat.id)
    except Exception:
        full_chat = chat

    member_count = None
    if full_chat.type in {"group", "supergroup", "channel"}:
        try:
            member_count = await context.bot.get_chat_member_count(full_chat.id)
        except Exception:
            member_count = None

    lines: list[str] = [
        f"id: {full_chat.id}",
        f"type: {full_chat.type}",
    ]

    title = getattr(full_chat, "title", None)
    if title:
        lines.append(f"title: {title}")

    username = getattr(full_chat, "username", None)
    if username:
        lines.append(f"username: @{username}")

    if member_count is not None:
        lines.append(f"members: {member_count}")

    invite_link = getattr(full_chat, "invite_link", None)
    if invite_link:
        lines.append(f"invite_link: {invite_link}")

    await update.effective_message.reply_text("\n".join(lines))


def _pressify_new_group_url() -> str:
    cfg = load_config()
    base = (cfg.get("endpoint_pressify") or "").strip()
    if not base:
        return ""
    return f"{base}/notification/assistants/new_group"


async def _post_json(url: str, payload: dict) -> tuple[int | None, str]:
    cfg = load_config()
    user_agent = (cfg.get("pressify_user_agent") or "PressifyAssistantBot/1.0").strip()

    def _do() -> tuple[int | None, str]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        req.add_header("User-Agent", user_agent)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
            return e.code, body
        except Exception as e:
            return None, str(e)

    return await asyncio.to_thread(_do)


async def _build_new_group_payload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    chat = update.effective_chat
    if not chat:
        return None

    try:
        full_chat = await context.bot.get_chat(chat.id)
    except Exception:
        full_chat = chat

    chat_type = getattr(full_chat, "type", "") or ""
    title = getattr(full_chat, "title", None) or getattr(chat, "title", None) or ""

    invite_link = getattr(full_chat, "invite_link", None)
    if not invite_link:
        username = getattr(full_chat, "username", None)
        if username:
            invite_link = f"https://t.me/{username}"

    if not invite_link and chat_type in {"group", "supergroup"}:
        try:
            link = await context.bot.create_chat_invite_link(full_chat.id)
            invite_link = getattr(link, "invite_link", None)
        except Exception:
            invite_link = None

    if not invite_link:
        invite_link = "no_invite_link"

    return {
        "id_group": str(full_chat.id),
        "type": str(chat_type),
        "title_group": str(title),
        "invite_link": str(invite_link),
    }


async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = _pressify_new_group_url()
    if not url:
        await update.effective_message.reply_text("Missing ENDPOINT_SYSTEM_PRESSIFY in .env")
        return

    payload = await _build_new_group_payload(update, context)
    if not payload:
        return

    status, body = await _post_json(url, payload)
    if status is None:
        await update.effective_message.reply_text(f"Setup failed!")
        return

    message = None
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            message = parsed.get("message")
    except Exception:
        message = None

    if message:
        await update.effective_message.reply_text(str(message))
        return

    await update.effective_message.reply_text(body[:1500])


async def my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_member_update = update.my_chat_member
    if not chat_member_update:
        return

    old_status = getattr(chat_member_update.old_chat_member, "status", None)
    new_status = getattr(chat_member_update.new_chat_member, "status", None)
    if old_status in {"left", "kicked"} and new_status in {"member", "administrator"}:
        url = _pressify_new_group_url()
        if not url:
            return
        payload = await _build_new_group_payload(update, context)
        if not payload:
            return
        await _post_json(url, payload)
