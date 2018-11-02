from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from sqlalchemy.types import ARRAY


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    length = db.Column(db.Integer)
    width = db.Column(db.Integer)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    departments = db.relationship('Department', backref='owner', lazy='dynamic')
    plans = db.relationship('Plan', backref='owner', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(140))
    employees = db.Column(db.Integer)
    size = db.Column(db.Integer)
    adjacency = db.Column(db.String(),default="[]")
    def __repr__(self):
        return '<Department {}>'.format(self.name)

class Plan(db.Model):
    # database metadata:
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # genotype data:
    definition = db.Column(db.String())

    room_def = db.Column(db.String())
    split_list = db.Column(db.String())
    dir_list = db.Column(db.String())
    room_order = db.Column(db.String())

    min_opening = db.Column(db.Integer)
    generation = db.Column(db.Integer)

    # scoring:
    pareto = db.Column(db.Integer, default = 0)
    crowding_score = db.Column(db.Integer, default = 0)
    dominated_count = db.Column(db.Integer, default = 0)
    adjacency_score = db.Column(db.Integer, default = 0)
    split_score = db.Column(db.Integer, default = 0)

    # geometry:
    edges_out = db.Column(db.String(), default="[]")
    dominates_these = db.Column(db.String(), default="[]")
    dist = db.Column(db.Integer, default = 0)

    def __repr__(self):
        return '<Floor plan {} of genereation {}.>'.format(self.id,self.generation)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
