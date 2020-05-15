from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flaskblog import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    liked = db.relationship('PostLike',foreign_keys='PostLike.user_id', backref='user', lazy='dynamic')
    saved = db.relationship('PostSave',foreign_keys='PostSave.user_id', backref='user', lazy='dynamic')

    unliked = db.relationship('PostUnLike',foreign_keys='PostUnLike.user_id', backref='user', lazy='dynamic')
    commented = db.relationship('PostComment',foreign_keys='PostComment.user_id',backref='user',lazy='dynamic')
    image = db.relationship('PostComment',foreign_keys='PostComment.user_id',backref='img',lazy=True)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    followed = db.relationship('Follow',
                               foreign_keys='Follow.follower_id',
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys='Follow.followed_id',
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

#----------------------------------------------------------------------------------
#follow
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

#---------------------------------------------------------------------------
#like
    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.id,
            PostLike.post_id == post.id).count() > 0


    def like1_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()


    def unlike_post(self, post):
        if not self.has_unliked_post(post):
            unlike = PostUnLike(user_id=self.id,post_id=post.id)
            db.session.add(unlike)

    def unlike1_post(self, post):
        if self.has_unliked_post(post):
            PostUnLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()


    def has_unliked_post(self, post):
        return PostUnLike.query.filter(
            PostUnLike.user_id == self.id,
            PostUnLike.post_id == post.id).count() > 0

#---------------------------------------------------------------------------------------------
#save
    def save_post(self, post):
        if not self.has_saved_post(post):
            save = PostSave(user_id=self.id, post_id=post.id)
            db.session.add(save)

    def has_saved_post(self, post):
        return PostSave.query.filter(
            PostSave.user_id == self.id,
            PostSave.post_id == post.id).count() > 0


    def unsave_post(self, post):
        if self.has_saved_post(post):
            PostSave.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    
#------------------------------------------------------------------------------------

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}','{self.confirmed}')"


class Post(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')
    unlikes = db.relationship('PostUnLike', backref='post', lazy='dynamic')
    comments = db.relationship('PostComment',backref='post',lazy='dynamic')
    saves = db.relationship('PostSave', backref='post', lazy='dynamic')

    image = db.Column(db.String(100))


    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}','{self.comments}','{self.image}')"  

class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return f"Like('{self.user_id}','{self.post_id}')"    
   
class PostUnLike(db.Model):
    __tablename__ = 'post_unlike'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return f"Unlike('{self.user_id}','{self.post_id}')"    

class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(20), db.ForeignKey('user.username'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    
    def __repr__(self):
        return f"Comment('{self.user_id}','{self.post_id}','{self.date_posted}','{self.content}')"    

class Follow(db.Model):
    __tablename__ = 'follows'    
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Follow('{self.follower_id}','{self.followed_id}')"



class PostSave(db.Model):
    __tablename__ = 'post_save'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return f"Save('{self.user_id}','{self.post_id}')"  



    