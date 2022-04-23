from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import dbHelper
from botinterface.flow import Flow
from customLogging import get_logger, INFO, ERROR
from params import root_dir, tokens

logger = get_logger('telegram', path=root_dir, log_level=5)

token = tokens['api']

"""
    each user can only have one active flow at a time
    when normal text received, check if flow is active for user, if not, ignore text
    on receive a command from user, remove flow for user
"""
flows = dict()


def remove_flow(user_id):
    if user_id in flows:
        del flows[user_id]


def log(user_id, level, message):
    logger.log(level, f'{user_id} | {message}')


def basic(update):
    user_id = update.effective_chat.id
    username = update.effective_chat.username

    user_pk = dbHelper.create_user(user_id, username)

    return user_pk, user_id, username


def start(update, context):
    user_pk, user_id, username = basic(update)
    remove_flow(user_id)

    log(username, INFO, 'Command received [start/help].')

    message_text = "I will help you create and manage short urls." \
                   "\n\nCommands you can use:" \
                   "\n\n    /new - Create a new short URL." \
                   "\n    /list - List all URLs create by you." \
                   "\n\nReport issues at t.me/siddhantkushwaha"
    context.bot.send_message(chat_id=user_id, text=message_text)


def new(update, context):
    user_pk, user_id, username = basic(update)
    remove_flow(user_id)

    log(username, INFO, 'Command received [new].')

    flow = Flow(user_id=user_id, flow_type='new_url', expected_keys={
        'full_url': 'Alright. Send me the URL you want to teenify.',
        'alias': 'What do you want the URL to look like?'
    })
    flows[user_id] = flow

    handle_flow(user_pk, user_id, username, None, context, flow)


def text(update, context):
    user_pk, user_id, username = basic(update)
    message = update.message.text

    flow = flows.get(user_id, None)
    if flow is not None:
        handle_flow(user_pk, user_id, username, message, context, flow)
    else:
        context.bot.send_message(chat_id=user_id, text="What are you trying to do?")

    log(username, INFO, 'Text received.')


def handle_flow(user_pk, user_id, username, message, context, flow):
    if flow.next_key is not None and message is not None:
        log(username, INFO, f'Received [{message} for [{flow.type}:{flow.next_key}].')
        flow.keys[flow.next_key] = message

    expected_key = None
    for key in flow.expected_keys:
        if flow.keys.get(key, None) is None:
            expected_key = key
            break

    if expected_key is None:

        """
            When all data is collected for a flow, it will have to be handled here
        """
        if flow.type == 'new_url':

            alias = flow.keys['alias']
            full_url = flow.keys['full_url']

            in_use_user_pk = dbHelper.is_alias_in_use(alias)
            if in_use_user_pk > 0:
                log(username, INFO, f'Alias [{alias}] already exists for [{in_use_user_pk}].')
                expected_key = 'alias'
                if in_use_user_pk != user_pk:
                    flow.expected_keys[expected_key] = 'URL already in use by someone.'
                else:
                    flow.expected_keys[expected_key] = 'URL already in use by you. Either delete that or send another.'
            else:
                dbHelper.create_url(
                    user_pk,
                    full_url,
                    alias
                )
                log(username, INFO, f'Created new alias [{alias}] for url [{full_url}].')
                context.bot.send_message(chat_id=user_id, text=f'Created.')

                remove_flow(user_id)

        else:
            log(username, ERROR, f'Unknown flow type [{flow.type}].')

    if expected_key is not None:
        flow.next_key = expected_key
        context.bot.send_message(chat_id=user_id, text=flow.expected_keys[expected_key])


if __name__ == '__main__':
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))

    dispatcher.add_handler(CommandHandler('new', new))
    dispatcher.add_handler(CommandHandler('list', start))

    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text))

    updater.start_polling()

    updater.idle()
    updater.stop()
