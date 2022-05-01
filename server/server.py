from datetime import datetime

from flask import Flask, redirect, request

import dbHelper
from db.database import get_db

app = Flask(__name__)

db = get_db()


def redirect_to_alias(visitor, alias):
    url = dbHelper.get_url(alias)
    if url is not None:

        # visitor tracking feature is only for non-random URLs
        if not url.is_random:
            dbHelper.update_visitor(url.id, visitor)

        if ((datetime.utcnow() - url.timestamp).total_seconds() // 86400) >= 7:
            url.timestamp = datetime.utcnow()
            dbHelper.update_url(url)

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
    app.run(host='0.0.0.0', port=6546)
