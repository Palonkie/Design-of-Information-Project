from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Ohhhhh! Spooky because it is secret!'
app.config["DEBUG"] = True

bootstrap = Bootstrap(app)

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="FMPortal",
    password="p@ssw0rd",
    hostname="FMPortal.mysql.pythonanywhere-services.com",
    databasename="FMPortal$fmportal",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(80))
    name = db.Column(db.String(80))
    telephone = db.Column(db.String(20))
    photoID = db.Column(db.Integer)
    usertype = db.Column(db.String(8))
    boothname = db.Column(db.String(200))
    website = db.Column(db.String(200))
    isActive = db.Column(db.Boolean(), default=True, nullable=False)
    isLocked = db.Column(db.Boolean(), default=False, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    usertype = SelectField('User type', choices=[('Customer', 'Customer'), ('Seller', 'Seller')])



@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('order'))

    return render_template('login.html', form=form)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, usertype=form.usertype.data, isActive=True, isLocked=False)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/order', methods=["GET", "POST"])
@login_required
def order():
    return render_template('order.html', name=current_user.username, type=current_user.usertype)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
