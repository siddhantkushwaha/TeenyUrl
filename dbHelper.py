from db.database import get_db
from db.models import User

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
