"""
    Telegram event handlers
"""
import sys
import logging
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
)

from dtb.celery import app  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN, DEBUG

from tgbot.handlers.utils import files, error
from tgbot.handlers.admin import handlers as admin_handlers
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.handlers.onboarding.manage_data import START, BALANCE, BUY_OR_DECLINE, FASOFKA, READY, OPLATIT, CONFIRM, \
    DISTRICT, KLAD_TYPE, READYC, DISTRICTC, FASOFKAC, KLAD_TYPEC, BUY_OR_DECLINEC, CONFIRM_ZK, CITIESC
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST
from tgbot.handlers.broadcast_message.static_text import broadcast_command, referral_command


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    # onboarding
    dp.add_handler(CommandHandler("start", onboarding_handlers.command_start))

    dp.add_handler(
        CallbackQueryHandler(onboarding_handlers.city_decision_handler, pattern=f"^{START}")
    )

    # city
    dp.add_handler(CommandHandler("change_city", onboarding_handlers.command_city_change))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.city_decision_handler, pattern=f"^{START}"))

    # product_ready
    dp.add_handler(CommandHandler("product_ready", onboarding_handlers.command_product_ready))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.product_chosen_handler_district, pattern=f"^{READY}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.fasofka_handler, pattern=f"^{DISTRICT}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.klad_type_handler, pattern=f"^{FASOFKA}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.ready_decision_handler, pattern=f"^{KLAD_TYPE}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.buy_or_decline_handler, pattern=f"^{BUY_OR_DECLINE}"))


    # product_to_order
    dp.add_handler(CommandHandler("product_to_order", onboarding_handlers.command_product_to_order))
    # временно
    #dp.add_handler(CallbackQueryHandler(onboarding_handlers.ready_decision_handler, pattern=f"^{READY}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.buy_or_decline_handler, pattern=f"^{BUY_OR_DECLINE}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.fasofka_handler, pattern=f"^{FASOFKA}"))
    # dp.add_handler(CallbackQueryHandler(onboarding_handlers.oplata_handler, pattern=f"^{CONFIRM}"))

    # account
    dp.add_handler(CommandHandler("account", onboarding_handlers.command_account))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.make_up_balance, pattern=f"^{BALANCE}"))


    # support
    dp.add_handler(CommandHandler("support", onboarding_handlers.command_support))
    dp.add_handler(
        MessageHandler(Filters.regex(r'^HELP'),
                        onboarding_handlers.receive_support_message)
    )

    # broadcast message
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{referral_command}(/s)?.*'), broadcast_handlers.broadcast_command_with_message)
    )
    dp.add_handler(
        CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    )

    # files
    dp.add_handler(MessageHandler(
        Filters.animation, files.show_file_id,
    ))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    # add product
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.c_product_chosen_handler_district, pattern=f"^{READYC}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.c_fasofka_handler, pattern=f"^{DISTRICTC}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.c_klad_type_handler, pattern=f"^{FASOFKAC}"))
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.received_klad_next_step_handler, pattern=f"^{KLAD_TYPEC}"))

    # dp.add_handler(CallbackQueryHandler(onboarding_handlers.c_citi_chosen_district_handler, pattern=f"^{CITIESC}"))

    dp.add_handler(
        MessageHandler(Filters.regex(f'^((\-?|\+?)?\d+(\.\d+)?),\s*((\-?|\+?)?\d+(\.\d+)?)$'),
                       onboarding_handlers.log_lat_handler)
    )
    dp.add_handler(
        MessageHandler(Filters.regex(f'^ОПИСАНИЕ '),
                       onboarding_handlers.description_handler)
    )
    dp.add_handler(
        MessageHandler(Filters.photo,
                       onboarding_handlers.location_photo_handler)
    )
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.confirm_zk_handler, pattern=f"^{CONFIRM_ZK}"))

    return dp


def run_pooling():
    """ Run bot in pooling mode """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = Bot(TELEGRAM_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    # it is really useful to send '👋' emoji to developer
    # when you run local test
    # bot.send_message(text='👋', chat_id=<YOUR TELEGRAM ID>)

    updater.start_polling()
    updater.idle()


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Запустить бота 🚀',
            'support': 'Поддержка',
            'change_city': 'Сменить город',
            'product_ready': 'Товары в наличии',
            'product_to_order': 'Товары под заказ',
            'account': 'Аккаунт и баланс',
        },
        'ru': {
            'start': 'Запустить бота 🚀',
            'support': 'Поддержка',
            'change_city': 'Сменить город',
            'product_ready': 'Товары в наличии',
            'product_to_order': 'Товары под заказ',
            'account': 'Аккаунт и баланс',
        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in langs_with_commands[language_code].items()
            ]
        )


# WARNING: it's better to comment the line below in DEBUG mode.
# Likely, you'll get a flood limit control error, when restarting bot too often
set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
