from datetime import datetime

from db.database import get_db
from db.models import User, URL, Visitor


def create_user(user_id, username):
    db = get_db()
    users = db.session.query(User).filter(User.user_id == user_id).all()
    if len(users) == 0:
        user = User(user_id=user_id, username=username, paid_amount=0)
    else:
        user = users[0]
        user.username = username

    db.session.merge(user)
    db.session.commit()

    return user


def get_user(user_id):
    db = get_db()
    users = db.session.query(User).filter(User.user_id == user_id).all()
    if len(users) == 0:
        return None
    return users[0]


def create_url(user_pk, full_url, alias, is_random):
    db = get_db()
    url = URL()
    url.full_url = full_url
    url.alias = alias
    url.user_id = user_pk
    url.is_random = is_random

    db.session.merge(url)
    db.session.commit()

    return url


def update_url(url):
    db = get_db()
    db.session.merge(url)
    db.session.commit()


def get_url(alias):
    db = get_db()
    urls = db.session.query(URL).filter(URL.alias == alias).all()
    if len(urls) == 0:
        return None
    return urls[0]


def is_alias_in_use(alias):
    db = get_db()
    results = db.session.query(URL).filter(URL.alias == alias).all()
    if len(results) > 0:
        return results[0].user_id
    return 0


def get_aliases(user_pk):
    db = get_db()
    urls = db.session.query(URL).filter(URL.user_id == user_pk).all()
    return urls


def delete_url_by_alias(user_pk, alias):
    db = get_db()
    url = get_url(alias)
    if url is not None:
        if url.user_id == user_pk:
            db.session.query(URL).filter(URL.id == url.id).delete()
            db.session.commit()


def update_visitor(url_pk, visitor_ip):
    db = get_db()
    visitors = db.session.query(Visitor).filter((Visitor.ip == visitor_ip) & (Visitor.url_id == url_pk)).all()
    if len(visitors) > 0:
        visitor = visitors[0]
        visitor.timestamp = datetime.utcnow()
    else:
        visitor = Visitor(ip=visitor_ip, url_id=url_pk)

    db.session.merge(visitor)
    db.session.commit()
