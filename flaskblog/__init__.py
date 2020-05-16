import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail


MAX_SEARCH_RESULTS = 50
app = Flask(__name__)
app.config['SECRET_KEY'] =os.urandom(16)
app.config['WHOOSH_BASE']='whoosh'
app.config['SECURITY_PASSWORD_SALT']= 'my_precious_two'
app.config['SQLALCHEMY_DATABASE_URI']='postgres://rmckyjrelemmlh:3138e8523cd6c897ea38f12ee5617afb4b2174234a602cc8c343062ecd0ff57a@ec2-52-7-39-178.compute-1.amazonaws.com:5432/d7gocrfuhfvthk'
#app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'mindflowingblog@gmail.com' 
app.config['MAIL_PASSWORD'] = 'mfuuwujgzsmnsijn'
mail = Mail(app)

from flaskblog import routes