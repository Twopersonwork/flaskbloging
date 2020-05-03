import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] =os.urandom(16)
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://mikzfzlqcrjrop:3d45f4f616d96f3c2912dc5666f1ae6310cfed045b7327e91cec7ea0f92dcf55@ec2-54-159-112-44.compute-1.amazonaws.com:5432/deh1r3ipd2n8v2'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'heybuddy471@gmail.com' 
app.config['MAIL_PASSWORD'] = 'syrfnzbvwdwwosgs'
mail = Mail(app)

from flaskblog import routes