from datetime import datetime

from flask import Flask, redirect, request

import dbHelper

app = Flask(__name__)


def redirect_to_alias(visitor, alias):
    db_helper = dbHelper.DbHelper()
    url = db_helper.get_url(alias)
    if url is not None:

        # visitor tracking feature is only for non-random URLs
        if not url.is_random:
            db_helper.update_visitor_for_url(url.id, visitor)

        if ((datetime.utcnow() - url.timestamp).total_seconds() // 86400) >= 7:
            url.timestamp = datetime.utcnow()
            db_helper.update(url)

        return redirect(url.full_url)
    else:
        return f'No url found for {alias}.'


@app.route('/<alias>')
def visit_v1(alias):
    return redirect_to_alias(request.remote_addr, alias)


@app.route('/<a1>/<a2>')
def visit_v2(a1, a2):
    return redirect_to_alias(request.remote_addr, f'{a1}/{a2}')


def run():
    app.run(host='0.0.0.0', port=80)
