from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from bot import init_db, handle_commands, button, help_command, API_TOKEN

def main() -> None:
    init_db()
    updater = Updater(API_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", handle_commands))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_commands))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    print("Bot is running...")
    updater.start_polling()
    updater.idle()