from flask import Flask, redirect, request

import dbHelper
from db.database import get_db

app = Flask(__name__)

db = get_db()


@app.route('/<alias>')
def visit(alias):
    visitor_ip = request.remote_addr

    url = dbHelper.get_url(alias)
    if url is not None:
        return redirect(url.full_url)
    else:
        return f'No url found for {alias}.'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
