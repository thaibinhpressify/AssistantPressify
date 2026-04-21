import os

from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN. Put it in .env or environment variables.")
    endpoint_pressify = os.getenv("ENDPOINT_SYSTEM_PRESSIFY", "").strip()
    if endpoint_pressify.endswith("/"):
        endpoint_pressify = endpoint_pressify[:-1]
    pressify_user_agent = os.getenv("PRESSIFY_USER_AGENT", "PressifyAssistantBot/1.0").strip()
    return {
        "token": token,
        "endpoint_pressify": endpoint_pressify,
        "pressify_user_agent": pressify_user_agent,
    }
