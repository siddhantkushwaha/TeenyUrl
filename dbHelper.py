from datetime import datetime

from db.database import get_db
from db.models import User, URL, Visitor


class DbHelper:

    def __init__(self):
        self.db = get_db()

    def update(self, obj):
        updated_obj = self.db.session.merge(obj)
        self.db.session.commit()
        obj.id = updated_obj.id

    def create_user(self, user_id, username=''):
        users = self.db.session.query(User).filter(User.user_id == user_id).all()
        if username is None or len(username) == 0:
            username = str(user_id)
        if len(users) == 0:
            user = User(user_id=user_id, username=username, paid_amount=0)
        else:
            user = users[0]
            user.username = username

        self.update(user)

        return user

    def get_user(self, user_id):
        users = self.db.session.query(User).filter(User.user_id == user_id).all()
        if len(users) == 0:
            return None
        return users[0]

    def create_url(self, user_pk, full_url, alias, is_random):
        url = URL()
        url.full_url = full_url
        url.alias = alias
        url.user_id = user_pk
        url.is_random = is_random

        self.update(url)

        return url

    def get_url(self, alias):
        urls = self.db.session.query(URL).filter(URL.alias == alias).all()
        if len(urls) == 0:
            return None
        return urls[0]

    def is_alias_in_use(self, alias):
        results = self.db.session.query(URL).filter(URL.alias == alias).all()
        if len(results) > 0:
            return results[0].user_id
        return 0

    def get_aliases(self, user_pk, is_random=None):
        urls = self.db.session.query(URL).filter(URL.user_id == user_pk)
        if is_random is not None:
            urls = urls.filter(URL.is_random == is_random)
        urls = urls.all()
        return urls

    def delete_url_by_alias(self, user_pk, alias):
        url = self.get_url(alias)
        if url is not None:
            if url.user_id == user_pk:
                self.db.session.query(URL).filter(URL.id == url.id).delete()
                self.db.session.commit()

    def update_visitor_for_url(self, url_pk, visitor_ip):
        visitors = self.db.session.query(Visitor).filter((Visitor.ip == visitor_ip) & (Visitor.url_id == url_pk)).all()
        if len(visitors) > 0:
            visitor = visitors[0]
            visitor.timestamp = datetime.utcnow()
        else:
            visitor = Visitor(ip=visitor_ip, url_id=url_pk)

        self.update(visitor)
