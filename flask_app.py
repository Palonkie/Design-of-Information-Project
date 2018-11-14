import datetime
import os
from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SelectField, DecimalField, SubmitField, HiddenField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_uploads import UploadSet, configure_uploads
from PIL import Image

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

photos = UploadSet('photos', extensions=('jpg', 'jpeg'))

app.config['UPLOADED_PHOTOS_DEST'] = 'mysite/static/img'
configure_uploads(app, photos)

# open on Wednesdays and Saturdays
OPENDAYS = [2, 5]

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))

class User(UserMixin, db.Model):
    __tablename__ = "user"
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

class Product(db.Model):
    __tablename__ = "product"
    productID = db.Column(db.Integer, primary_key=True)
    sellerID = db.Column(db.Integer)
    description = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    unitprice = db.Column(db.Float)
    photoID = db.Column(db.Integer)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

class Available(db.Model):
    __tablename__ = "available"
    offerID = db.Column(db.Integer, primary_key=True)
    productID = db.Column(db.Integer)
    sellerID = db.Column(db.Integer)
    day = db.Column(db.DateTime)
    quantity = db.Column(db.Float)
    offerprice = db.Column(db.Float)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

class OrderTbl(db.Model):
    __tablename__ = "ordertbl"
    orderID = db.Column(db.Integer, primary_key=True)
    offerID = db.Column(db.Integer)
    custID = db.Column(db.Integer)
    quantity = db.Column(db.Float)
    wishlist = db.Column(db.Float)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)


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
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat password')
    usertype = SelectField('User type', choices=[('Customer', 'Customer'), ('Seller', 'Seller')])

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[Length(max=100)])
    telephone = StringField('Telephone', validators=[Length(max=20)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=100)])
    boothname = StringField('Booth name', validators=[Length(max=200)])
    website = StringField('Web site address', validators=[Length(max=200)])
    submit = SubmitField('Save profile data')

class NewProductForm(FlaskForm):
    description = StringField('Product description', validators=[InputRequired(), Length(max=100)])
    unit = StringField('Sell-by unit', validators=[InputRequired(), Length(max=20)])
    unitprice = DecimalField('Price ($) per unit', validators=[InputRequired()])

class SelectProductForm(FlaskForm):
    product = SelectField('Select a product', coerce=int)
    submitselect = SubmitField('Select')

class EditProductForm(FlaskForm):
    description = StringField('Product description', validators=[InputRequired(), Length(max=100)])
    unit = StringField('Sell-by unit', validators=[InputRequired(), Length(max=20)])
    unitprice = DecimalField('Price ($) per unit', validators=[InputRequired()])
    submit = SubmitField('Update product information')

class PhotoForm(FlaskForm):
    photo = FileField(validators=[FileRequired()])
    submitphoto = SubmitField('Upload')

class AvailableForm(FlaskForm):
    date = SelectField('On which day will you sell?')
    product = SelectField('Select product to sell', coerce=int)
    quantity = DecimalField('How many available on this day?', validators=[InputRequired()])
    submit = SubmitField('Add product to available list')

class OrderItemForm(FlaskForm):
    offerid = HiddenField('offerid')
    quantity = DecimalField('Quantity to order', default=0)
    wishlist = DecimalField('Quantity for wish list', default=0)

class DateSelectForm(FlaskForm):
    date = SelectField('Day')
    submitdate = SubmitField('Select Date')

class SearchForm(FlaskForm):
    string = StringField('Search')
    submitsearch = SubmitField('Search')


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
            else:
                flash('Incorrect password', 'error')
                return redirect(url_for('login'))
        else:
            flash('Incorrect username', 'error')
            return redirect(url_for('login'))

    return render_template('login.html', form=form, error='none')

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
    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    o = db.session.query(OrderTbl.offerID, db.func.sum(OrderTbl.quantity).label('ordertotal')).group_by(OrderTbl.offerID).all()

    if 'ordersearch' in session:
        q = db.session.query(Available, Product, User).join(Product, Available.productID==Product.productID).join(User, Available.sellerID==User.id).filter(Available.day==session['day'], Product.description.contains(session['ordersearch'])).all()
        # above returns a list of tuples of the table row objects e.g. [(<Available 1>, <Product 2>, <User 1>), (<Available 6>, <Product 3>, <User 2>), ... ]
        session.pop('ordersearch', None)
        session.modified = True
    else:
        q = db.session.query(Available, Product, User).join(Product, Available.productID==Product.productID).join(User, Available.sellerID==User.id).filter(Available.day==session['day']).all()
        # above returns a list of tuples of the table row objects e.g. [(<Available 1>, <Product 2>, <User 1>), (<Available 6>, <Product 3>, <User 2>), ... ]

    form = DateSelectForm()
    datelist = []
    d = datetime.date.today()
    for i in range(14):
        if d.weekday() in OPENDAYS:
            datelist.append((d.strftime('%Y-%m-%d'), d.strftime('%a %b %d, %Y')))
        d = d + datetime.timedelta(1)
    form.date.choices = datelist

    formsearch = SearchForm()

    if form.submitdate.data and form.validate_on_submit():
        session['day'] = form.date.data
        session.modified = True
        return redirect(url_for('order'))

    if formsearch.submitsearch.data and formsearch.validate_on_submit():
        if len(formsearch.string.data) > 0:
            session['ordersearch'] = formsearch.string.data
            session.modified = True
            return redirect(url_for('order'))
        else:
            if 'ordersearch' in session:
                session.pop('ordersearch', None)
            return redirect(url_for('order'))

    return render_template('order.html', availablelist=q, ordertotal=dict(o), day=session['day'], formdate=form, formsearch=formsearch)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    user = User.query.filter_by(username=current_user.username).first()
    form = ProfileForm(obj=user)
    formphoto = PhotoForm()
    if os.path.exists('mysite/static/img/U' + str(user.id) + '.png'):
        photofile = '/static/img/U' + str(user.id) + ".png?" + str(os.path.getmtime('mysite/static/img/U' + str(user.id) + '.png'))
    else:
        photofile = '/static/img/default.png'
    if form.submit.data and form.validate_on_submit():
        setattr(user, 'name', form.name.data)
        setattr(user, 'telephone', form.telephone.data)
        setattr(user, 'email', form.email.data)
        if user.usertype == 'Seller':
            setattr(user, 'boothname', form.boothname.data)
            setattr(user, 'website', form.website.data)
        db.session.commit()
        flash('Your profile information has been updated', 'success')
        return redirect(url_for('profile'))
    elif formphoto.submitphoto.data and formphoto.validate_on_submit():
        if 'photo' in request.files:
            filename = photos.save(request.files['photo'],name='temp.')
            SIZE = (150,200)
            im = Image.open('mysite/static/img/' + filename)
            im.convert('RGB')
            im.thumbnail(SIZE, Image.ANTIALIAS)
            pad = Image.new('RGBA', SIZE, (255, 255, 255, 0))
            pad.paste(im, (int((SIZE[0] - im.size[0]) / 2), int((SIZE[1] - im.size[1]) / 2)))
            pad.save('mysite/static/img/U' + str(user.id) + '.png', 'PNG')
            if os.path.exists('mysite/static/img/temp.jpg'):
                os.remove('mysite/static/img/temp.jpg')
            elif os.path.exists('mysite/static/img/temp.jpeg'):
                os.remove('mysite/static/img/temp.jpeg')
            flash('Your photo has been uploaded', 'success')
            return redirect(url_for('profile'))

    return render_template('profile.html', form=form, formphoto=formphoto, usertype=user.usertype, photofile=photofile)

@app.route('/newproduct', methods=["GET", "POST"])
@login_required
def newproduct():
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))
    form = NewProductForm()
    if form.validate_on_submit():
        new_prod = Product(sellerID=user.id, description=form.description.data, unit=form.unit.data, unitprice=form.unitprice.data, isDeleted=False)
        db.session.add(new_prod)
        db.session.commit()
        flash('You successfully added ' + form.description.data, 'success')
        return redirect(url_for('newproduct'))

    return render_template('newproduct.html', form=form)

@app.route('/editproduct', defaults={'id': None}, methods=["GET", "POST"])
@app.route('/editproduct/<id>', methods=["GET", "POST"])
@login_required
def editproduct(id):
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    products = Product.query.filter_by(sellerID=user.id).order_by(Product.description).all()

    if products == None:
        return redirect(url_for('producterror'))

    productlist = [(p.productID, p.description) for p in products]

    formselect = SelectProductForm()
    formselect.product.choices = productlist

    if id == None:
        id = productlist[0][0]

    thisproduct = Product.query.filter_by(sellerID=user.id, productID=id).first()
    if thisproduct:
            form = EditProductForm(obj=thisproduct)
    else:
        return redirect(url_for('producterror'))

    formphoto = PhotoForm()
    if os.path.exists('mysite/static/img/P' + str(id) + '.png'):
        photofile = '/static/img/P' + str(id) + ".png?" + str(os.path.getmtime('mysite/static/img/P' + str(id) + '.png'))
    else:
        photofile = '/static/img/defaultproduct.png'

    if formselect.submitselect.data and formselect.validate_on_submit():
        return redirect(url_for('editproduct', id=formselect.product.data))
    if form.submit.data and form.validate_on_submit():
        setattr(thisproduct, 'description', form.description.data)
        setattr(thisproduct, 'unit', form.unit.data)
        setattr(thisproduct, 'unitprice', form.unitprice.data)
        db.session.commit()
        flash('Product information has been updated', 'success')
        return redirect(url_for('editproduct', id=id))
    elif formphoto.submitphoto.data and formphoto.validate_on_submit():
        if 'photo' in request.files:
            filename = photos.save(request.files['photo'],name='ptemp.')
            SIZE = (120,90)
            im = Image.open('mysite/static/img/' + filename)
            im.convert('RGB')
            im.thumbnail(SIZE, Image.ANTIALIAS)
            pad = Image.new('RGBA', SIZE, (255, 255, 255, 0))
            pad.paste(im, (int((SIZE[0] - im.size[0]) / 2), int((SIZE[1] - im.size[1]) / 2)))
            pad.save('mysite/static/img/P' + str(id) + '.png', 'PNG')
            if os.path.exists('mysite/static/img/ptemp.jpg'):
                os.remove('mysite/static/img/ptemp.jpg')
            elif os.path.exists('mysite/static/img/ptemp.jpeg'):
                os.remove('mysite/static/img/ptemp.jpeg')
            flash('Your photo has been uploaded', 'success')
            return redirect(url_for('editproduct', id=id))

    return render_template('editproduct.html', form=form, formphoto=formphoto, formselect=formselect, photofile=photofile, id=id)


@app.route('/available', methods=["GET", "POST"])
@login_required
def available():
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))
    datelist = []
    d = datetime.date.today()
    for i in range(14):
        if d.weekday() in OPENDAYS:
            datelist.append((d.strftime('%Y-%m-%d'), d.strftime('%a %b %d, %Y')))
        d = d + datetime.timedelta(1)
    products = Product.query.filter_by(sellerID=user.id).order_by(Product.description).all()
    productlist = [(p.productID, p.description + ' - $' + '%.2f' % p.unitprice + ' per ' + p.unit) for p in products]
    form = AvailableForm()
    form.date.choices = datelist
    form.product.choices = productlist
    availablelist = Available.query.filter_by(sellerID=user.id).join(Product, Available.productID==Product.productID).add_columns(Product.description, Product.unit).all()
    # above returns a list of tuples of the Available row objects and the added columns e.g. [(<Available 1>, .description, .unit), (<Available 6>, .description, .unit), ... ]
    if form.submit.data and form.validate_on_submit():
        p = Product.query.filter_by(productID=form.product.data).first()
        new_available = Available(productID=form.product.data, sellerID=user.id, day=datetime.datetime.strptime(form.date.data,'%Y-%m-%d'), quantity=form.quantity.data, offerprice=p.unitprice, isDeleted=False)
        db.session.add(new_available)
        db.session.commit()
        flash('You successfully added a product', 'success')
        return redirect(url_for('available'))

    return render_template('available.html', form=form, availablelist=availablelist)

@app.route('/orderitem/<id>', methods=["GET"])
@login_required
def orderitem(id):
    available = Available.query.filter_by(offerID=id).first()
    product = Product.query.filter_by(productID=available.productID).first()
    seller = User.query.filter_by(id=available.sellerID).first()
    ordered = OrderTbl.query.filter_by(offerID=id)
    ordertotal = 0
    if ordered:
        for order in ordered:
            ordertotal += order.quantity
    remaining = available.quantity - ordertotal

    form = OrderItemForm()

    return render_template('orderitem.html', available=available, product=product, seller=seller, remaining=remaining, form=form)

@app.route('/placeorder', methods=["POST"])
@login_required
def placeorder():
    form = OrderItemForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        new_order = OrderTbl(offerID=form.offerid.data, custID=user.id, quantity=form.quantity.data, wishlist=form.wishlist.data, isDeleted=False)
        db.session.add(new_order)
        db.session.commit()

    return redirect(url_for('order'))

@app.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    user = User.query.filter_by(username=current_user.username).first()

    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    dayalt=datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%a %b %d, %Y')

    q = (db.session.query(OrderTbl, Available, Product, User)
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .join(User, Available.sellerID==User.id)
        .filter(OrderTbl.custID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .all())
    # above returns a list of tuples of the table row objects
    # e.g. [(<OrderTbl 1>, <Available 1>, <Product 2>, <User 1>), (<OrderTbl 3>, <Available 6>, <Product 3>, <User 2>), ... ]

    form = DateSelectForm()
    datelist = []
    d = datetime.date.today()
    for i in range(14):
        if d.weekday() in OPENDAYS:
            datelist.append((d.strftime('%Y-%m-%d'), d.strftime('%a %b %d, %Y')))
        d = d + datetime.timedelta(1)
    form.date.choices = datelist

    if form.submitdate.data and form.validate_on_submit():
        session['day'] = form.date.data
        session.modified = True
        return redirect(url_for('cart'))

    return render_template('cart.html', itemlist=q, day=session['day'], dayalt=dayalt, formdate=form)

@app.route('/deleteorderitem/<id>', methods=["GET"])
@login_required
def deleteorderitem(id):
    order = OrderTbl.query.filter_by(orderID=id).first()
    setattr(order, 'isDeleted', True)
    db.session.commit()

    return redirect(url_for('cart'))

@app.route('/notseller', methods=["GET", "POST"])
@login_required
def notseller():
    if request.method == 'POST':
        return redirect(url_for('order'))
    return render_template('notseller.html')

@app.route('/producterror', methods=["GET", "POST"])
@login_required
def producterror():
    if request.method == 'POST':
        return redirect(url_for('order'))
    return render_template('producterror.html')

