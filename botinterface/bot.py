from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import dbHelper
import helper
from botinterface.botHelper import remove_flow, log, create_url, delete_url, flows
from botinterface.flow import Flow
from customLogging import INFO, ERROR
from params import tokens

token = tokens['api']


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
                   "\n/list - List all URLs created by you." \
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
    if user.paid_amount > 0 or user.id == 1:
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

    message_text = 'URLs created by you:\n\n'
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
            expected_key = create_url(user, context, flow)
        elif flow.type == 'delete_url':
            expected_key = delete_url(user, context, flow)

        else:
            log(user.username, ERROR, f'Unknown flow type [{flow.type}].')

    if expected_key is not None:
        flow.next_key = expected_key
        context.bot.send_message(chat_id=user.user_id, text=flow.expected_keys[expected_key][0])


def run():
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
