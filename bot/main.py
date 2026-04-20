import logging

from telegram.ext import ApplicationBuilder, ChatMemberHandler, CommandHandler

if __package__:
    from .commands import chatinfo, help_cmd, hook, my_chat_member, setup, start
    from .config import load_config
else:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from bot.commands import chatinfo, help_cmd, hook, my_chat_member, setup, start
    from bot.config import load_config


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )

    cfg = load_config()
    app = ApplicationBuilder().token(cfg["token"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("hook", hook))
    app.add_handler(CommandHandler("chatinfo", chatinfo))
    app.add_handler(CommandHandler("setup", setup))
    app.add_handler(ChatMemberHandler(my_chat_member, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))

    app.run_polling(allowed_updates=["message", "my_chat_member"])


if __name__ == "__main__":
    main()
