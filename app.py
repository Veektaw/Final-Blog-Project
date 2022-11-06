from enum import unique
from multiprocessing import context
from unicodedata import name
from flask import Flask, redirect, render_template, request, url_for, flash, session
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from flask_login import LoginManager
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
import uuid

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)


app.config['SECRET_KEY'] = '9e6e82e501e740149e01727700939800'
app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///' + os.path.join(base_dir,'blog.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    __tablename__ = "users"

    
    id = db.Column(db.Integer(), primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False, unique=True)
    posted_by = db.relationship("Blogpost", back_populates='post_by', lazy="dynamic")

    def __repr__(self):
        return f'<User {self.username}>'

class Blogpost(db.Model, UserMixin):
     __tablename__ = "blogposts"


     id = db.Column(db.Integer(), primary_key=True)
     title = db.Column(db.String(100), nullable=False)
     content = db.Column(db.Text(), nullable=False)
     posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)
     author = db.Column(db.String, nullable=False)
     post_by = db.relationship("User", back_populates="posted_by")
   


     def __repr__(self):
        return f'<User {self.title}>'
  


##### This is to show all posts that have been created ######
@app.route("/")
def home():
    blogs = Blogpost.query.all()
    context = {"blogs": blogs}

    return render_template('home.html', **context)


##### This is to create a new post ######
@app.route("/create_post/new", methods=['GET', 'POST'])
def create_post():

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = current_user.id
        author = current_user.username

        new_post = Blogpost(title=title, content=content, author=author, user_id=user_id )

        
### Adds post to the database ###
        db.session.add(new_post)
        db.session.commit()
        flash("Success! Blog created")


#### This redirects the user back to the homepage when they post the blog ####
        return redirect(url_for('home'))

      
    return render_template('create_post.html')


### This gives the user the ability to view individual blogs ####
@app.route('/view_blogs/<int:blog_id>/', methods=["GET", "POST"])
def blog(blog_id):
    blog = Blogpost.query.get_or_404(blog_id)
    return render_template('view_blogs.html', blog=blog)

##### This is to edit an already posted blog ####
@app.route("/edit_blog/<int:id>", methods=["GET", "POST"])
@login_required
def edit_blog(id):
    blog = Blogpost.query.get_or_404(id)
    if request.method == 'POST':
        blog.title = request.form['title']
        blog.content = request.form['content']
        
        db.session.commit()
        flash("Success! Blog edited")
        return redirect(url_for('home', id=blog.id))

        context = {'blog': blog}
    
    return render_template('edit_blog.html', blog=blog)


#### This is to delete a blog ####
@app.route("/delete/<int:id>/", methods=["GET", "POST"])
@login_required
def delete_blog(id):
    blog_to_delete = Blogpost.query.get_or_404(id)

    db.session.delete(blog_to_delete)
    db.session.commit()
    flash("Success! Blog deleted")
    return redirect(url_for('home'))


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


##### This is to sign in user ######
@app.route("/signin", methods=['GET', 'POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        flash(f'Success!! Welcome {username}')
        login_user(user)
        return redirect(url_for('home'))
    
    if user and not check_password_hash(user.password, password):
        flash("Credentials do not match", category="error")
        return redirect(url_for('signin'))
    
    
    return render_template('signin.html')

### This is to sign up ####
@app.route("/signup", methods=['GET', 'POST'])
def signup():
        if request.method == 'POST':
            fullname = request.form.get('fullname')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user:
                flash("Username taken", category="error")
                return redirect(url_for('signup'))

            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash("Email already registred", category="error")
                return redirect(url_for('signup'))

            password_hash = generate_password_hash(password)

            new_user = User(fullname=fullname, username=username, email=email, password=password_hash)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created")
            return redirect(url_for('signin'))

        return render_template('signup.html')


@app.route('/protected')
@login_required
def protected():
    return render_template('protected.html', name=current_user)

##### This is to log out the user ######
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    flash('Goodbye')
    logout_user()

    return redirect(url_for('home'))


#### This is supposed to send it back to homepage when the user clicks submit, not sure i got it right #####
@app.route("/contact") #methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Message sent")
        return redirect(url_for('home'))
    return render_template('contact.html')

#### These is for about page ####
@app.route("/about")
def about():
    return render_template('about.html')



if __name__ =='__main__':
    app.run(debug=True)
