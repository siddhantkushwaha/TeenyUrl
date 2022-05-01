import helper
import params
from customLogging import INFO, get_logger

logger = get_logger('telegram', path=params.root_dir, log_level=5)

"""
    each user can only have one active flow at a time
    when normal text received, check if flow is active for user, if not, ignore text
    on receive a command from user, remove flow for user
"""
flows = dict()


def log(user_id, level, message):
    logger.log(level, f'{user_id} | {message}')


def remove_flow(user_id):
    if user_id in flows:
        del flows[user_id]


def create_url(db_helper, user, context, flow):
    expected_key = None

    alias = flow.keys['alias']
    if alias.lower() == 'random':
        alias = helper.get_random_alias()
        is_random = True

        # update keys
        flow.keys['alias'] = alias
        flow.keys['is_random'] = is_random

    full_url = flow.keys['full_url']
    is_random = flow.keys['is_random']

    is_alias_valid = True
    if alias.count('/') > 1:
        is_alias_valid = False

    in_use_user_pk = db_helper.is_alias_in_use(alias)

    if full_url.find(params.domain) > -1:
        log(user.username, INFO, f'Loops not allowed [{full_url}].')

        expected_key = 'full_url'
        flow.expected_keys[expected_key][0] = "What you're trying to do is not allowed 🧐. Enter another URL."

    elif not is_alias_valid:

        if not is_random:
            log(user.username, INFO, f'Invalid alias [{alias}].')
            expected_key = 'alias'
            flow.expected_keys[expected_key][0] = f"Invalid. {alias} has unsupported characters. Try again."
        else:
            # impossible situation though
            log(user.username, INFO, f'Random alias [{alias}] invalid!')
            context.bot.send_message(chat_id=user.user_id, text=f'There was problem, try again?')

    elif in_use_user_pk > 0:

        if not is_random:
            log(user.username, INFO, f'Alias [{alias}] already exists for [{in_use_user_pk}].')
            expected_key = 'alias'
            if in_use_user_pk != user.id:
                flow.expected_keys[expected_key][0] = \
                    'URL already in use by someone.'
            else:
                flow.expected_keys[expected_key][0] = \
                    'URL already in use by you. Either delete that or send another.'
        else:
            log(user.username, INFO, f'Random alias [{alias}] conflicted!')
            context.bot.send_message(chat_id=user.user_id, text=f'There was problem, try again?')

    else:

        db_helper.create_url(
            user.id,
            full_url,
            alias,
            is_random
        )
        log(user.username, INFO, f'Created new alias [{alias}] for url [{full_url}].')
        context.bot.send_message(chat_id=user.user_id, text=f'Created. {params.hostname}/{alias}')

        remove_flow(user.user_id)

    return expected_key


def delete_url(db_helper, user, context, flow):
    expected_key = None

    alias = flow.keys['alias']
    confirmation = flow.keys['confirmation'].lower()

    if confirmation not in ['yes', 'no']:

        log(user.username, INFO, f'Invalid reply.')
        expected_key = 'confirmation'
        flow.expected_keys[expected_key][
            0] = f"Didn't get it, should I delete the URL for {alias} or not? Yes/No?"

    else:

        if confirmation == 'yes':
            db_helper.delete_url_by_alias(
                user.id,
                alias
            )
            log(user.username, INFO, f'Deleted [{alias}] from user [{user.id}].')
            context.bot.send_message(chat_id=user.user_id, text=f'Deleted.')

        remove_flow(user.user_id)

    return expected_key


def update_quota(db_helper, user, context, flow):
    expected_key = None

    shared_user_id = flow.keys['user_id']
    paid_amount = int(flow.keys['paid_amount'])

    shared_user = db_helper.create_user(shared_user_id)
    shared_user.paid_amount += paid_amount
    db_helper.update(shared_user)

    context.bot.send_message(
        chat_id=user.user_id,
        text=f'Updated paid amount to : {int(shared_user.paid_amount)}.'
    )

    context.bot.send_message(
        chat_id=shared_user_id,
        text=f'Your quota has been updated. Total URLs you can create : {int(5 * shared_user.paid_amount)}.'
    )

    return expected_key


def has_quota(db_helper, user):
    return int(5 * user.paid_amount) > len(db_helper.get_aliases(user.id, is_random=False))
