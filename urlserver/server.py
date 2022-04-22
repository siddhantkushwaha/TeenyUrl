from flask import Flask, redirect, request

from db.database import get_db
from db.models import URL

app = Flask(__name__)

db = get_db()


@app.route('/<alias>')
def visit(alias):
    visitor_ip = request.remote_addr

    urls = db.session.query(URL).filter(URL.alias == alias).all()

    if len(urls) > 0:

        url_to_visit = urls[0].fullurl
        return redirect(url_to_visit)

    else:
        return f'No url found for {alias}.'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
