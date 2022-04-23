from telegram.ext import Updater, CommandHandler

import dbHelper
from customLogging import get_logger, INFO
from params import root_dir, tokens

logger = get_logger('telegram', path=root_dir, log_level=5)

token = tokens['api']


def log(user_id, level, message):
    logger.log(level, f'{user_id} | {message}')


def start(update, context):
    user_id = update.effective_chat.id
    username = update.effective_chat.username

    dbHelper.create_user(user_id, username)

    log(username, INFO, 'Command received [start/help].')

    text = "I will help you create and manage short urls." \
           "\n\nCommands you can use:" \
           "\n\n /new - Create a new short URL." \
           "\n /list - List all URLs create by you." \
           "\n\nReport issues at t.me/siddhantkushwaha"
    context.bot.send_message(chat_id=user_id, text=text)


def new(update, context):
    user_id = update.effective_chat.id
    username = update.effective_chat.username

    dbHelper.create_user(user_id, username)

    log(username, INFO, 'Command received [new].')

    # Add logic here

    text = ""
    context.bot.send_message(chat_id=user_id, text=text)


"""
Template function to add a new command

def template_command(update, context):
    user_id = update.effective_chat.id
    username = update.effective_chat.username

    dbHelper.create_user(user_id, username)

    log(username, INFO, 'Command received [new].')

    # Add logic here

    text = ""
    context.bot.send_message(chat_id=user_id, text=text)
"""

if __name__ == '__main__':
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))

    dispatcher.add_handler(CommandHandler('new', start))
    dispatcher.add_handler(CommandHandler('list', start))

    updater.start_polling()

    updater.idle()
    updater.stop()
