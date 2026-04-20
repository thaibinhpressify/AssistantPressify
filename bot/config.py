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
    return {"token": token, "endpoint_pressify": endpoint_pressify}
