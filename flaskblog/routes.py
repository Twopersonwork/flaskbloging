import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort,current_app
from flaskblog import app, db, bcrypt, mail 
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm, PostCommentForm,SearchForm)
from flaskblog.models import User, Post,PostComment,Follow,PostLike,PostSave
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from flaskblog.token import generate_confirmation_token, confirm_token
from flaskblog import MAX_SEARCH_RESULTS
import flask_whooshalchemy as whooshalchemy

whooshalchemy.whoosh_index(app, Post)
whooshalchemy.whoosh_index(app,User)



@app.route("/home")
@login_required
def home():
    form=SearchForm()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts,form=form)

@app.route("/",methods=['GET'])
def intro():
    return render_template('lay.html', title='Home')

@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,confirmed=False)
        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('user/activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        flash('A confirmation email has been sent via email.', 'success')

        
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)







@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.confirmed:
        return redirect(url_for('home'))
    form = LoginForm()
    user = User.query.filter_by(email=form.email.data).first()
    if form.validate_on_submit() :
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.confirmed and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    elif request.method=='POST':
        flash('Please verify your email.','danger')
        
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('intro'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def save_images(form_photo):
    hash_photo = secrets.token_hex(10)
    _, file_extention = os.path.splitext(form_photo.filename)
    photo_name = hash_photo + file_extention
    file_path = os.path.join(current_app.root_path,'static/post_pics',photo_name)
    form_photo.save(file_path)
    return photo_name
    

@app.route("/account/edit", methods=['GET', 'POST'])
@login_required
def account_edit():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.commit()
        if current_user.email != form.email.data:
            current_user.email = form.email.data
            current_user.confirmed=False
            db.session.commit()
            token = generate_confirmation_token(form.email.data)
            confirm_url = url_for('confirm_email1', token=token, _external=True)
            html = render_template('user/updated.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(form.email.data, subject, html)
            flash('A confirmation email has been sent via email.', 'success')
            return redirect(url_for('login'))
        flash('Your account has been updated!', 'success')
        
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('edit_acc.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/account/<string:username>", methods=['GET', 'POST'])
@login_required
def account(username):
    user = User.query.filter_by(username=username).first_or_404()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    posts = Post.query.filter_by(author=user)
        
    return render_template('account.html',image_file=image_file,user=user,posts=posts)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.photo.data:
            form_photo = save_images(form.photo.data)
            post = Post(title=form.title.data, content=form.content.data, author=current_user,image=form_photo)
            db.session.add(post)
            db.session.commit()
        else:
            post = Post(title=form.title.data, content=form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')
            
@app.route("/post/<int:post_id>",methods=['GET','POST'])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostCommentForm()

    return render_template('post.html', title=post.title, post=post,form=form)

@app.route("/post/<int:post_id>/comment", methods=['GET', 'POST'])
@login_required
def post_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostCommentForm()
    if form.validate_on_submit():
        comment = PostComment(user_id=current_user.id,user_name=current_user.username,post_id=post.id,content=form.content.data) 
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
        return redirect(url_for('post_comment',post_id=post_id))
    return render_template('comment.html',
                           form=form,post=post)

                           


@app.route("/post/<int:post_id>/comment/<int:id>/cdelete", methods=['POST','GET'])
@login_required
def delete_comment(id,post_id):
    post = Post.query.get_or_404(post_id)
    comment = PostComment.query.get(id)
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('post_comment',post_id=post_id))
    return render_template('comment.html',post=post,comment=comment)



@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.photo.data:
            picture_file = save_images(form.photo.data)
            post.image = picture_file
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post',post=post)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like_post(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
    if action == 'like1':
        current_user.like1_post(post)
        db.session.commit()
    if action == 'unlike1':
        current_user.unlike1_post(post)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/save/<int:post_id>/<action>')
@login_required
def save_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'save':
        current_user.save_post(post)
        db.session.commit()
    if action == 'unsave':
        current_user.unsave_post(post)
        db.session.commit()
    return redirect(request.referrer)
    






@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    post = Post.query.filter_by(user_id=user.id).first()
    
    return render_template('user_posts.html', posts=posts, user=user,post=post)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('login'))



@app.route('/confirm1/<token>')
def confirm_email1(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('login'))

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_USERNAME']
    )
    mail.send(msg)



@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username),'success')
        return redirect(url_for('user_posts'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user_posts',username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username),'success')
    return redirect(url_for('user_posts',username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username),'success')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user_posts',username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username),'success')
    return redirect(url_for('user_posts',username=username))

@app.route('/like/<username>', methods=['GET'])
@login_required
def like_post(username):
    user =User.query.filter_by(username=username).first()
    if user == current_user:
        postlike = (db.session.query(PostLike.post_id).filter(PostLike.user_id==user.id))
        posts = (db.session.query(Post).filter(Post.id.in_(postlike)).all())
    
    return render_template('like_post.html', posts=posts,user=user)


@app.route('/save/<username>', methods=['GET'])
@login_required
def save_post(username):
    user =User.query.filter_by(username=username).first()
    if user == current_user:
        postsave = (db.session.query(PostSave.post_id).filter(PostSave.user_id==user.id))
        posts = (db.session.query(Post).filter(Post.id.in_(postsave)).all())
    
    return render_template('save_post.html', posts=posts,user=user)


@app.route('/search', methods=['POST'])
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('search_results', query=form.search.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
    if query==['username']:
        results = User.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
        return render_template('user_results.html',query=query,results=results)
    elif query==['title']:
        results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
        return render_template('search_results.html',query=query,results=results)
