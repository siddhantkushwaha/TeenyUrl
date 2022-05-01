from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import helper
import params
from botinterface.botHelper import remove_flow, log, create_url, delete_url, update_quota, flows, has_quota
from botinterface.flow import Flow
from customLogging import INFO, ERROR
from dbHelper import DbHelper
from params import tokens

token = tokens['api']


def basic(db_helper, update):
    user_id = update.effective_chat.id
    username = update.effective_chat.username

    user = db_helper.create_user(user_id, username)

    return user


def command_start(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [start/help].')

    message_text = "I will help you create and manage short urls." \
                   "\n\nCommands you can use:" \
                   "\n\n/new - Create a new short URL." \
                   "\n/list - List all URLs created by you." \
                   "\n/delete 1 - Delete first URL in the list shown by /list command." \
                   "\n/sub - To unlock paid features." \
                   "\n/help - Get help." \
                   f"\n\nReport issues at {params.config['admin_telegram_address']}"
    context.bot.send_message(chat_id=user.user_id, text=message_text)


def command_new(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [new].')

    expected_keys = {
        'full_url': ['Alright. Send me the URL you want to teenify.'],
    }

    # users who pay are allowed to decide what URLs can look like
    alias = None
    if user.id == 1 or has_quota(db_helper, user):
        expected_keys['alias'] = ["What do you want the URL to look like? Type 'random' to generate randomly."]
    else:
        alias = helper.get_random_alias()

    flow = Flow(user_id=user.user_id, flow_type='new_url', expected_keys=expected_keys)
    flow.keys['is_random'] = False

    if alias is not None:
        flow.keys['is_random'] = True
        flow.keys['alias'] = alias

    flows[user.user_id] = flow

    handle_flow(db_helper, user, None, context, flow)


def command_list(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [list].')

    urls = db_helper.get_aliases(user.id)
    if len(urls) > 0:
        message_text = 'URLs created by you:\n\n'
        idx = 1
        for url in urls:
            message_text += f'{idx}. {url.alias} : {url.full_url[:100]}\n'
            idx += 1
    else:
        message_text = 'You have not created any URLs yet.'

    context.bot.send_message(chat_id=user.user_id, text=message_text)


def command_delete(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [delete].')

    message = update.message.text

    invalid = True
    url_idx = message.replace('/delete', '').strip()
    if url_idx.isdigit():
        url_idx = int(url_idx) - 1
        urls = db_helper.get_aliases(user.id)
        if 0 <= url_idx < len(urls):
            invalid = False

            flow = Flow(user_id=user.user_id, flow_type='delete_url', expected_keys={
                'confirmation': [f'Are you sure you want to delete the URL for {urls[url_idx].alias}? Yes/No?'],
            })
            flow.keys['alias'] = urls[url_idx].alias
            flows[user.user_id] = flow

            handle_flow(db_helper, user, None, context, flow)

    if invalid:
        message_text = "You didn't use the command properly. Use '/list' first and then do '/delete 1' to delete first URL in the list."
        context.bot.send_message(chat_id=user.user_id, text=message_text)


def command_sub(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    remove_flow(user.user_id)

    log(user.username, INFO, 'Command received [sub].')

    message_text = "Pay via Crypto:" \
                   "\n20 DOGE for 5 named URLs of your choice, 40 for 10, 100 for 50." \
                   "\n\nPay via UPI:" \
                   "\nRs. 200 for 5 named URLs of your choice, 400 for 10, 2000 for 50." \
                   "\n\nAfter quota is exceeded, delete a named URL or random urls will be created." \
                   "\n\nUPI and DOGE wallet addresses will be shared below this message." \
                   f"\n\nSend a proof of payment at {params.config['admin_telegram_address']}."
    context.bot.send_message(chat_id=user.user_id, text=message_text)

    message_text = params.config['wallet']['upi']
    context.bot.send_message(chat_id=user.user_id, text=message_text)

    message_text = params.config['wallet']['doge']
    context.bot.send_message(chat_id=user.user_id, text=message_text)


def text(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    message = update.message.text

    flow = flows.get(user.user_id, None)
    if flow is not None:
        handle_flow(db_helper, user, message, context, flow)
    else:
        context.bot.send_message(chat_id=user.user_id, text="What are you trying to do?")

    log(user.username, INFO, 'Text received.')


def contact(update, context):
    db_helper = DbHelper()

    user = basic(db_helper, update)
    if user.id == 1:
        shared_user_id = update.message.contact.user_id
        flow = Flow(user_id=user.user_id, flow_type='update_quota', expected_keys={
            'paid_amount': [
                f'How many units did this user pay? Remember, 1 unit = 5 named URLs. '
                f'This will be added to existing quota.'],
        })
        flow.keys['user_id'] = shared_user_id
        flows[user.user_id] = flow

        handle_flow(db_helper, user, None, context, flow)
    else:
        context.bot.send_message(chat_id=user.user_id, text="What are you trying to do?")


def handle_flow(db_helper, user, message, context, flow):
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
            expected_key = create_url(db_helper, user, context, flow)
        elif flow.type == 'delete_url':
            expected_key = delete_url(db_helper, user, context, flow)
        elif flow.type == 'update_quota':
            expected_key = update_quota(db_helper, user, context, flow)
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
    dispatcher.add_handler(CommandHandler('sub', command_sub))

    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text))

    dispatcher.add_handler(MessageHandler(Filters.contact, contact))

    updater.start_polling()

    updater.idle()
    updater.stop()
