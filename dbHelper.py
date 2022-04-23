from db.database import get_db
from db.models import User, URL

db = get_db()


def create_user(user_id, username):
    users = db.session.query(User).filter(User.user_id == user_id).all()
    if len(users) == 0:
        user = User(user_id=user_id, username=username, paid_amount=0)
    else:
        user = users[0]
        user.username = username

    db.session.merge(user)
    db.session.commit()

    return user.id


def create_url(user_pk, full_url, alias):
    url = URL()
    url.full_url = full_url
    url.alias = alias
    url.user_id = user_pk

    db.session.merge(url)
    db.session.commit()

    return url.id


def is_alias_in_use(alias):
    results = db.session.query(URL).filter(URL.alias == alias).all()
    if len(results) > 0:
        return results[0].user_id
    return 0
