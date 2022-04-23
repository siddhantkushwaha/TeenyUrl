import dbHelper
import params
from botinterface.bot import log, remove_flow
from customLogging import INFO


def create_url(user, context, flow):
    expected_key = None

    alias = flow.keys['alias']
    full_url = flow.keys['full_url']
    is_random = flow.keys['is_random']

    is_alias_valid = True
    if alias.count('/') > 1:
        is_alias_valid = False

    in_use_user_pk = dbHelper.is_alias_in_use(alias)

    if not is_alias_valid:

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

        dbHelper.create_url(
            user.id,
            full_url,
            alias,
            is_random
        )
        log(user.username, INFO, f'Created new alias [{alias}] for url [{full_url}].')
        context.bot.send_message(chat_id=user.user_id, text=f'Created. {params.hostname}/{alias}')

        remove_flow(user.user_id)

    return expected_key


def delete_url(user, context, flow):
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
            dbHelper.delete_url_by_alias(
                user.id,
                alias
            )
            log(user.username, INFO, f'Deleted [{alias}] from user [{user.id}].')
            context.bot.send_message(chat_id=user.user_id, text=f'Deleted.')

        remove_flow(user.user_id)

    return expected_key
