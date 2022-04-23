from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import dbHelper
import helper
import params
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

    user = dbHelper.create_user(user_id, username)

    return user


def command_start(update, context):
    user = basic(update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [start/help].')

    message_text = "I will help you create and manage short urls." \
                   "\n\nCommands you can use:" \
                   "\n\n/new - Create a new short URL." \
                   "\n/list - List all URLs create by you." \
                   "\n/delete 1 - Delete first URL in the list shown by /list command." \
                   "\n/help - Get help." \
                   "\n\nReport issues at t.me/siddhantkushwaha"
    context.bot.send_message(chat_id=user.user_id, text=message_text)


def command_new(update, context):
    user = basic(update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [new].')

    expected_keys = {
        'full_url': ['Alright. Send me the URL you want to teenify.'],
    }

    # users who pay are allowed to decide what URLs can look like
    alias = None
    if user.paid_amount > 0:
        expected_keys['alias'] = ['What do you want the URL to look like?']
    else:
        alias = helper.get_random_alias()

    flow = Flow(user_id=user.user_id, flow_type='new_url', expected_keys=expected_keys)
    flow.keys['is_random'] = False

    if alias is not None:
        flow.keys['is_random'] = True
        flow.keys['alias'] = alias

    flows[user.user_id] = flow

    handle_flow(user, None, context, flow)


def command_list(update, context):
    user = basic(update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [list].')

    urls = dbHelper.get_aliases(user.id)

    message_text = 'URLs create by you:\n\n'
    idx = 1
    for url in urls:
        message_text += f'{idx}. {url.alias} : {url.full_url[:100]}\n'
        idx += 1

    context.bot.send_message(chat_id=user.user_id, text=message_text)


def command_delete(update, context):
    user = basic(update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [delete].')

    message = update.message.text

    invalid = True
    url_idx = message.replace('/delete', '').strip()
    if url_idx.isdigit():
        url_idx = int(url_idx) - 1
        urls = dbHelper.get_aliases(user.id)
        if 0 <= url_idx < len(urls):
            invalid = False

            flow = Flow(user_id=user.user_id, flow_type='delete_url', expected_keys={
                'confirmation': [f'Are you sure you want to delete the URL for {urls[url_idx].alias}? Yes/No?'],
            })
            flow.keys['alias'] = urls[url_idx].alias
            flows[user.user_id] = flow

            handle_flow(user, None, context, flow)

    if invalid:
        message_text = "You didn't use the command properly. Use '/list' first and then do '/delete 1' to delete first URL in the list."
        context.bot.send_message(chat_id=user.user_id, text=message_text)


def text(update, context):
    user = basic(update)
    message = update.message.text

    flow = flows.get(user.user_id, None)
    if flow is not None:
        handle_flow(user, message, context, flow)
    else:
        context.bot.send_message(chat_id=user.user_id, text="What are you trying to do?")

    log(user.username, INFO, 'Text received.')


def handle_flow(user, message, context, flow):
    if flow.next_key is not None and message is not None:
        log(user.username, INFO, f'Received [{message} for [{flow.type}:{flow.next_key}].')
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
            is_random = flow.keys['is_random']

            in_use_user_pk = dbHelper.is_alias_in_use(alias)
            if in_use_user_pk > 0:
                if not is_random:

                    log(user.username, INFO, f'Alias [{alias}] already exists for [{in_use_user_pk}].')
                    expected_key = 'alias'
                    if in_use_user_pk != user.id:
                        flow.expected_keys[expected_key][0] = 'URL already in use by someone.'
                    else:
                        flow.expected_keys[expected_key][
                            0] = 'URL already in use by you. Either delete that or send another.'

                else:

                    log(user.username, INFO, f'Random alis [{alias}] conflicted!')
                    context.bot.send_message(chat_id=user.user_id, text=f'There was problem, try again?')

            else:
                dbHelper.create_url(
                    user.id,
                    full_url,
                    alias,
                    is_random
                )
                log(user.username, INFO, f'Created new alias [{alias}] for url [{full_url}].')
                context.bot.send_message(chat_id=user.user_id, text=f'Created. {params.hostname}/{alias}')

                remove_flow(user.user_id)

        elif flow.type == 'delete_url':

            alias = flow.keys['alias']
            confirmation = flow.keys['confirmation'].lower()

            if confirmation not in ['yes', 'no']:
                log(user.username, INFO, f'Invalid reply.')
                expected_key = 'confirmation'
                flow.expected_keys[expected_key][
                    0] = f"Didn't get it, should I delete the URL for {alias} or not? Yes/No?"
            else:
                if confirmation == 'yes':
                    dbHelper.delete_url_by_alias(
                        user.id,
                        alias
                    )
                    log(user.username, INFO, f'Deleted [{alias}] from user [{user.id}].')
                    context.bot.send_message(chat_id=user.user_id, text=f'Deleted.')

                remove_flow(user.user_id)

        else:
            log(user.username, ERROR, f'Unknown flow type [{flow.type}].')

    if expected_key is not None:
        flow.next_key = expected_key
        context.bot.send_message(chat_id=user.user_id, text=flow.expected_keys[expected_key][0])


if __name__ == '__main__':
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', command_start))
    dispatcher.add_handler(CommandHandler('help', command_start))

    dispatcher.add_handler(CommandHandler('new', command_new))
    dispatcher.add_handler(CommandHandler('list', command_list))
    dispatcher.add_handler(CommandHandler('delete', command_delete))

    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text))

    updater.start_polling()

    updater.idle()
    updater.stop()
