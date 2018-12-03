import datetime
import os
from flask import Flask, redirect, render_template, request, url_for, flash, session, Markup
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SelectField, DecimalField, SubmitField, HiddenField
from wtforms.validators import InputRequired, Email, Length, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_uploads import UploadSet, configure_uploads
from PIL import Image
from flask_mail import Mail, Message

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

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
#app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = 'fmportalvt@gmail.com'
app.config['MAIL_PASSWORD'] = 'owhbwpttaatlzisf'
app.config['MAIL_DEFAULT_SENDER'] = 'Blacksburg Farmers Market Portal <fmportalvt@gmail.com>'
app.config['MAIL_MAX_EMAILS'] = None
#app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)

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
    email = db.Column(db.String(100))
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
    description = StringField('Product name', validators=[InputRequired(), Length(max=100)])
    unit = StringField('Sell-by unit', validators=[InputRequired(), Length(max=20)])
    unitprice = DecimalField('Price ($) per unit', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Save product information')

class SelectProductForm(FlaskForm):
    product = SelectField('Select a product', coerce=int)
    submitselect = SubmitField('Select')

class EditProductForm(FlaskForm):
    description = StringField('Product description', validators=[InputRequired(), Length(max=100)])
    unit = StringField('Sell-by unit', validators=[InputRequired(), Length(max=20)])
    unitprice = DecimalField('Price ($) per unit', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Update product information')

class PhotoForm(FlaskForm):
    photo = FileField(validators=[FileRequired()])
    submitphoto = SubmitField('Upload photo')

class AvailableForm(FlaskForm):
    product = SelectField('Select product to sell', coerce=int)
    quantity = DecimalField('How many available on this day?', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Add product to available list')

class EditAvailableForm(FlaskForm):
    offerid = HiddenField('offerid')
    date = StringField('Selling on')
    description = StringField('Product')
    unit = StringField('Sell-by unit')
    quantity = DecimalField('Quantity available on this day? (Enter 0 to delete)', validators=[InputRequired(), NumberRange(min=0)])
    offerprice = DecimalField('Price ($) per unit', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Update information')

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
        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            flash('The Username or Email given has been used on a previous account', 'error')
            return redirect(url_for('register'))
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/order', methods=["GET", "POST"])
@login_required
def order():
    user = User.query.filter_by(username=current_user.username).first()

    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    o = db.session.query(OrderTbl.offerID, db.func.sum(OrderTbl.quantity).label('ordertotal')).group_by(OrderTbl.offerID).all()

    if 'ordersearch' in session:
        q = (db.session.query(Available, Product, User)
            .join(Product, Available.productID==Product.productID)
            .join(User, Available.sellerID==User.id)
            .filter(Available.day==session['day'], Product.description.contains(session['ordersearch']), Available.isDeleted==False)
            .all())
        # above returns a list of tuples of the table row objects e.g. [(<Available 1>, <Product 2>, <User 1>), (<Available 6>, <Product 3>, <User 2>), ... ]
        session.pop('ordersearch', None)
        session.modified = True
    else:
        q = (db.session.query(Available, Product, User)
            .join(Product, Available.productID==Product.productID)
            .join(User, Available.sellerID==User.id)
            .filter(Available.day==session['day'], Available.isDeleted==False)
            .all())
        # above returns a list of tuples of the table row objects e.g. [(<Available 1>, <Product 2>, <User 1>), (<Available 6>, <Product 3>, <User 2>), ... ]

    cartnum = (db.session.query(OrderTbl, Available)
        .join(Available, OrderTbl.offerID==Available.offerID)
        .filter(OrderTbl.custID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .count())

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

    return render_template('order.html', availablelist=q, ordertotal=dict(o), day=session['day'], formdate=form, formsearch=formsearch, cartnum=cartnum, usertype=current_user.usertype)

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

    if form.submit.data and form.validate_on_submit():
        new_prod = Product(sellerID=user.id, description=form.description.data, unit=form.unit.data, unitprice=form.unitprice.data, isDeleted=False)
        db.session.add(new_prod)
        db.session.commit()
        flash(Markup('You successfully added ' + form.description.data + '. You can add a photo on the <strong>Edit Product</strong> page'), 'success')
        return redirect(url_for('newproduct'))

    return render_template('newproduct.html', form=form, usertype=current_user.usertype)

@app.route('/editproduct', defaults={'id': None}, methods=["GET", "POST"])
@app.route('/editproduct/<id>', methods=["GET", "POST"])
@login_required
def editproduct(id):
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    products = Product.query.filter_by(sellerID=user.id).order_by(Product.description).all()

    if products == []:
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

    return render_template('editproduct.html', form=form, formphoto=formphoto, formselect=formselect, photofile=photofile, id=id, usertype=current_user.usertype)


@app.route('/available', methods=["GET", "POST"])
@login_required
def available():
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    dayalt=datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%a %b %d, %Y')

    formdate = DateSelectForm()
    datelist = []
    d = datetime.date.today()
    for i in range(14):
        if d.weekday() in OPENDAYS:
            datelist.append((d.strftime('%Y-%m-%d'), d.strftime('%a %b %d, %Y')))
        d = d + datetime.timedelta(1)
    formdate.date.choices = datelist
    formdate.date.label = "On which day will you sell?"

    products = Product.query.filter_by(sellerID=user.id).order_by(Product.description).all()
    productlist = []
    for p in products:
        if p.unit.lower()[:2] == "ea":
            productlist.append((p.productID, p.description + ' - $' + '%.2f' % p.unitprice + ' ' + p.unit))
        else:
            productlist.append((p.productID, p.description + ' - $' + '%.2f' % p.unitprice + ' per ' + p.unit))

    form = AvailableForm()
    form.product.choices = productlist

    availablelist = (Available.query
        .filter_by(sellerID=user.id, day=session['day'], isDeleted=False)
        .join(Product, Available.productID==Product.productID)
        .add_columns(Product.description, Product.unit, Product.productID)
        .order_by(Product.description)
        .all())
    # above returns a list of tuples of the Available row objects and the added columns e.g. [(<Available 1>, .description, .unit, .productID), (<Available 6>, .description, .unit, .productID), ... ]

    if form.submit.data and form.validate_on_submit():
        p = Product.query.filter_by(productID=form.product.data).first()
        new_available = Available(productID=form.product.data, sellerID=user.id, day=datetime.datetime.strptime(session['day'],'%Y-%m-%d'), quantity=form.quantity.data, offerprice=p.unitprice, isDeleted=False)
        db.session.add(new_available)
        db.session.commit()
        flash('You successfully added a product', 'success')
        return redirect(url_for('available'))

    if formdate.submitdate.data and formdate.validate_on_submit():
        session['day'] = formdate.date.data
        session.modified = True
        return redirect(url_for('available'))

    return render_template('available.html', form=form, formdate=formdate, availablelist=availablelist, day=session['day'], dayalt=dayalt, usertype=current_user.usertype)

@app.route('/editavailable/<id>', methods=["GET", "POST"])
@login_required
def editavailable(id):
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    available = (Available.query
        .filter_by(offerID=id)
        .join(Product, Available.productID==Product.productID)
        .add_columns(Product.description, Product.unit)
        .first())
    # above returns a tuple of the Available product and the added columns e.g. (<Available>, .description, .unit)

    ordered = (db.session.query(db.func.sum(OrderTbl.quantity).label('quantity'))
        .filter(OrderTbl.offerID==id)
        .first())

    if ordered[0] is None:
        orderedqty = 0
    else:
        orderedqty = ordered[0]

    dayalt=available[0].day.strftime('%a %b %d, %Y')

    form = EditAvailableForm()
    if request.method == 'GET':
        form.offerid.data = id
        form.date.data = dayalt
        form.description.data = available.description
        form.unit.data = available.unit
        form.quantity.data = available[0].quantity
        form.offerprice.data = available[0].offerprice

    if form.submit.data and form.validate_on_submit():
        print(form.quantity.data)
        print(orderedqty)
        availableitem = Available.query.filter_by(offerID=form.offerid.data).first()
        if int(form.quantity.data) == 0 and int(orderedqty) == 0:
            setattr(availableitem, 'quantity', form.quantity.data)
            setattr(availableitem, 'offerprice', form.offerprice.data)
            setattr(availableitem, 'isDeleted', True)
            db.session.commit()
            return redirect(url_for('available'))
        if float(form.quantity.data) < float(orderedqty):
            flash('Quantity cannot be less than already ordered quantity of ' + str(orderedqty), 'error')
            return redirect(url_for('editavailable', id=form.offerid.data))
        else:
            setattr(availableitem, 'quantity', form.quantity.data)
            setattr(availableitem, 'offerprice', form.offerprice.data)
            db.session.commit()
            return redirect(url_for('available'))

    return render_template('editavailable.html', form=form, id=id, usertype=current_user.usertype)

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

    return render_template('orderitem.html', available=available, product=product, seller=seller, remaining=remaining, form=form, usertype=current_user.usertype)

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

    return render_template('cart.html', itemlist=q, day=session['day'], dayalt=dayalt, formdate=form, usertype=current_user.usertype)

@app.route('/ordersummary', methods=["GET", "POST"])
@login_required
def ordersummary():
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    dayalt=datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%a %b %d, %Y')

    q = (db.session.query(
        OrderTbl.quantity,
        OrderTbl.wishlist,
        Available.quantity.label('initial'),
        Available.offerprice,
        Product.productID,
        Product.description,
        Product.unit,
        (OrderTbl.quantity * Available.offerprice).label('itemtotal'))
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .filter(Available.sellerID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .subquery())

    qq = (db.session.query(
        db.func.sum(q.c.quantity).label('quantity'),
        db.func.sum(q.c.wishlist).label('wishlist'),
        q.c.initial,
        q.c.offerprice,
        q.c.productID,
        q.c.description,
        q.c.unit,
        db.func.sum(q.c.itemtotal).label('itemtotal'))
        .group_by(q.c.initial, q.c.offerprice, q.c.productID, q.c.description, q.c.unit)
        .all())

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
        return redirect(url_for('ordersummary'))

    return render_template('ordersummary.html', summarylist=qq, day=session['day'], formdate=form, usertype=current_user.usertype, store=current_user.boothname, dayalt=dayalt)

@app.route('/orderdetail', methods=["GET", "POST"])
@login_required
def orderdetail():
    user = User.query.filter_by(username=current_user.username).first()
    if user.usertype != 'Seller':
        return redirect(url_for('notseller'))

    if 'day' not in session:
        d = datetime.date.today()
        while d.weekday() not in OPENDAYS:
            d = d + datetime.timedelta(1)
        session['day'] = d.strftime('%Y-%m-%d')
        session.modified = True

    dayalt=datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%a %b %d, %Y')

    q = (db.session.query(
        OrderTbl.quantity,
        OrderTbl.wishlist,
        Available.offerprice,
        Product.description,
        Product.unit,
        (OrderTbl.quantity * Available.offerprice).label('itemtotal'),
        User.name)
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .join(User, OrderTbl.custID==User.id)
        .filter(Available.sellerID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .all())

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
        return redirect(url_for('orderdetail'))

    return render_template('orderdetail.html', detaillist=q, day=session['day'], formdate=form, usertype=current_user.usertype, store=current_user.boothname, dayalt=dayalt)

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
    return render_template('notseller.html', usertype=current_user.usertype)

@app.route('/producterror', methods=["GET", "POST"])
@login_required
def producterror():
    if request.method == 'POST':
        return redirect(url_for('order'))
    return render_template('producterror.html', usertype=current_user.usertype)

@app.route('/emailcart')
@login_required
def emailcart():
    user = User.query.filter_by(username=current_user.username).first()
    dayalt = datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%A %B %d, %Y')
    month = datetime.datetime.strptime(session['day'],'%Y-%m-%d').month
    weekday = datetime.datetime.strptime(session['day'],'%Y-%m-%d').weekday()
    if month in [4,5,6,7,8,9,10]:
        if weekday > 4:
            hours = "8am - 2pm"
        else:
            hours = "Noon - 6pm"
    elif month in [11,12]:
        if weekday > 4:
            hours = "9am - 2pm"
        else:
            hours = "Noon - 6pm"
    else:
        if weekday > 4:
            hours = "10am - 2pm"
        else:
            hours = "Noon - 6pm"

    q = (db.session.query(OrderTbl, Available, Product, User)
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .join(User, Available.sellerID==User.id)
        .filter(OrderTbl.custID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .all())
    # above returns a list of tuples of the table row objects
    # e.g. [(<OrderTbl 1>, <Available 1>, <Product 2>, <User 1>), (<OrderTbl 3>, <Available 6>, <Product 3>, <User 2>), ... ]

    msg = Message(recipients=[user.email])
    msg.subject = "Blacksburg Farmers Market Order - " + dayalt

    msg.html = "<img src='http://fmportal.pythonanywhere.com/static/img/fmLogo.png' /> &nbsp; <img src='http://fmportal.pythonanywhere.com/static/img/fmMailBanner.png' /><br><br>"

    msg.html = msg.html + "Hi " + user.name + ",<br><br>"
    msg.html = msg.html + "Thanks for ordering items at the Blacksburg Farmers Market on <strong>" + dayalt + "</strong><br><br>"
    msg.html = msg.html + "Here is a summary of your order.<br><br>"
    msg.html = msg.html + "<table style='border: 1px solid black; border-collapse: collapse;'>"

    carttotal = 0
    for item in q:
        itemtotal = item[0].quantity * item[1].offerprice
        carttotal = carttotal + itemtotal
        if item[2].unit.lower()[:2] == "ea":
            s = ""
            per = ""
        else:
            s = "s"
            per = "per "

        msg.html = msg.html + "<tr style='border: 1px solid black; border-collapse: collapse;'>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse;'><img src='http://fmportal.pythonanywhere.com/static/img/P" + str(item[2].productID) + ".png' onerror='http://fmportal.pythonanywhere.com/static/img/defaultproduct.png' /></td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item[2].description + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item[0].quantity) + " " + item[2].unit + s + "@ " + "${:.2f}".format(item[1].offerprice) + " " + per + item[2].unit + "<br><br>"
        msg.html = msg.html + "Item total = <strong>" + "${:.2f}".format(itemtotal) + "</strong></td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'><strong>" + item[3].boothname + "</strong><br>" + item[3].name + "<br>" + item[3].telephone + "</td></tr>"

    msg.html = msg.html + "</table><br>"
    msg.html = msg.html + "Your total for all ordered items is <strong>" + "${:.2f}".format(carttotal) + "</strong><br><br>"
    msg.html = msg.html + "We look forward to seeing you on " + dayalt + ". Remember that our hours that day are <strong>" + hours + "</strong>.<br>"
    msg.html = msg.html + "When you arrive, please look for vendor's names on the signs on the front of their tables or above their booths.<br><hr><br>"
    msg.html = msg.html + "<a href='http://blacksburgfarmersmarket.com/'>Blacksburg Farmers Market</a> - <a href='https://www.google.com/maps/d/viewer?mid=1MX2R9crBm_cUD8yoACS_z_K-uCU&ll=37.22836360418549%2C-80.41460575000002&z=19'>100 Draper Rd NW, Blacksburg, VA 24060</a>"

    mail.send(msg)

    return redirect(url_for('emailsuccess'))

@app.route('/emailsummary')
@login_required
def emailsummary():
    user = User.query.filter_by(username=current_user.username).first()
    dayalt = datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%A %B %d, %Y')
    month = datetime.datetime.strptime(session['day'],'%Y-%m-%d').month
    weekday = datetime.datetime.strptime(session['day'],'%Y-%m-%d').weekday()
    if month in [4,5,6,7,8,9,10]:
        if weekday > 4:
            hours = "8am - 2pm"
        else:
            hours = "Noon - 6pm"
    elif month in [11,12]:
        if weekday > 4:
            hours = "9am - 2pm"
        else:
            hours = "Noon - 6pm"
    else:
        if weekday > 4:
            hours = "10am - 2pm"
        else:
            hours = "Noon - 6pm"

    q = (db.session.query(
        OrderTbl.quantity,
        OrderTbl.wishlist,
        Available.quantity.label('initial'),
        Available.offerprice,
        Product.productID,
        Product.description,
        Product.unit,
        (OrderTbl.quantity * Available.offerprice).label('itemtotal'))
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .filter(Available.sellerID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .subquery())

    qq = (db.session.query(
        db.func.sum(q.c.quantity).label('quantity'),
        db.func.sum(q.c.wishlist).label('wishlist'),
        q.c.initial,
        q.c.offerprice,
        q.c.productID,
        q.c.description,
        q.c.unit,
        db.func.sum(q.c.itemtotal).label('itemtotal'))
        .group_by(q.c.initial, q.c.offerprice, q.c.productID, q.c.description, q.c.unit)
        .all())

    msg = Message(recipients=[user.email])
    msg.subject = "Blacksburg Farmers Market Reservation Summary - " + dayalt

    msg.html = "<img src='http://fmportal.pythonanywhere.com/static/img/fmLogo.png' /> &nbsp; <img src='http://fmportal.pythonanywhere.com/static/img/fmMailBanner.png' /><br><br>"

    msg.html = msg.html + "Hi " + user.name + ",<br><br>"
    msg.html = msg.html + "Here is a summary of all your items that have been reserved for <strong>" + dayalt + "</strong><br><br>"
    msg.html = msg.html + "<table style='border: 1px solid black; border-collapse: collapse;'>"
    msg.html = msg.html + "<tr style='border: 1px solid black; border-collapse: collapse;'>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Product</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Sell-by unit</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Initial quantity</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Reserved quantity</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Wish list quantity</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Unit price</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Total</th></tr>"

    ordertotal = 0
    for item in qq:
        itemtotal = item.quantity * item.offerprice
        ordertotal = ordertotal + itemtotal

        msg.html = msg.html + "<tr style='border: 1px solid black; border-collapse: collapse;'>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item.description + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item.unit + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item.initial) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item.quantity) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item.wishlist) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + "${:.2f}".format(item.offerprice) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + "${:.2f}".format(itemtotal) + "</td></tr>"

    msg.html = msg.html + "</table><br>"
    msg.html = msg.html + "Your total for all reserved items is <strong>" + "${:.2f}".format(ordertotal) + "</strong><br><br>"
    msg.html = msg.html + "If there is any quantity in the wish list column, and you can bring more than your stated initial quantity,<br>"
    msg.html = msg.html + "you will likely be able to sell the additional quantity in the wish list.<br><br>"
    msg.html = msg.html + "We look forward to having you sell on " + dayalt + ". Remember that our hours that<br>"
    msg.html = msg.html + "day are  <strong>" + hours + "</strong>.<br><hr><br>"
    msg.html = msg.html + "<a href='http://blacksburgfarmersmarket.com/'>Blacksburg Farmers Market</a> - <a href='https://www.google.com/maps/d/viewer?mid=1MX2R9crBm_cUD8yoACS_z_K-uCU&ll=37.22836360418549%2C-80.41460575000002&z=19'>100 Draper Rd NW, Blacksburg, VA 24060</a>"

    mail.send(msg)

    return redirect(url_for('emailsuccesssumm'))

@app.route('/emaildetail')
@login_required
def emaildetail():
    user = User.query.filter_by(username=current_user.username).first()
    dayalt = datetime.datetime.strptime(session['day'],'%Y-%m-%d').strftime('%A %B %d, %Y')
    month = datetime.datetime.strptime(session['day'],'%Y-%m-%d').month
    weekday = datetime.datetime.strptime(session['day'],'%Y-%m-%d').weekday()
    if month in [4,5,6,7,8,9,10]:
        if weekday > 4:
            hours = "8am - 2pm"
        else:
            hours = "Noon - 6pm"
    elif month in [11,12]:
        if weekday > 4:
            hours = "9am - 2pm"
        else:
            hours = "Noon - 6pm"
    else:
        if weekday > 4:
            hours = "10am - 2pm"
        else:
            hours = "Noon - 6pm"

    q = (db.session.query(
        OrderTbl.quantity,
        OrderTbl.wishlist,
        Available.offerprice,
        Product.description,
        Product.unit,
        (OrderTbl.quantity * Available.offerprice).label('itemtotal'),
        User.name)
        .join(Available, OrderTbl.offerID==Available.offerID)
        .join(Product, Available.productID==Product.productID)
        .join(User, OrderTbl.custID==User.id)
        .filter(Available.sellerID==user.id, OrderTbl.isDeleted==False, Available.day==session['day'])
        .all())

    msg = Message(recipients=[user.email])
    msg.subject = "Blacksburg Farmers Market Reservation Details - " + dayalt

    msg.html = "<img src='http://fmportal.pythonanywhere.com/static/img/fmLogo.png' /> &nbsp; <img src='http://fmportal.pythonanywhere.com/static/img/fmMailBanner.png' /><br><br>"

    msg.html = msg.html + "Hi " + user.name + ",<br><br>"
    msg.html = msg.html + "Here is a detailed list of all the customers who have made reservations for your items and what they have<br>"
    msg.html = msg.html + "reserved for <strong>" + dayalt + "</strong><br><br>"
    msg.html = msg.html + "<table style='border: 1px solid black; border-collapse: collapse;'>"
    msg.html = msg.html + "<tr style='border: 1px solid black; border-collapse: collapse;'>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Customer</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Product</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Sell-by unit</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Reserved quantity</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Wish list quantity</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Unit price</th>"
    msg.html = msg.html + "<th style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>Total</th></tr>"

    for item in q:
        itemtotal = item.quantity * item.offerprice

        msg.html = msg.html + "<tr style='border: 1px solid black; border-collapse: collapse;'>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item.name + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item.description + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + item.unit + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item.quantity) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + str(item.wishlist) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + "${:.2f}".format(item.offerprice) + "</td>"
        msg.html = msg.html + "<td style='border: 1px solid black; border-collapse: collapse; padding: 15px;'>" + "${:.2f}".format(itemtotal) + "</td></tr>"

    msg.html = msg.html + "</table><br>"
    msg.html = msg.html + "We look forward to having you sell on " + dayalt + ". Remember that our hours that<br>"
    msg.html = msg.html + "day are  <strong>" + hours + "</strong>.<br><hr><br>"
    msg.html = msg.html + "<a href='http://blacksburgfarmersmarket.com/'>Blacksburg Farmers Market</a> - <a href='https://www.google.com/maps/d/viewer?mid=1MX2R9crBm_cUD8yoACS_z_K-uCU&ll=37.22836360418549%2C-80.41460575000002&z=19'>100 Draper Rd NW, Blacksburg, VA 24060</a>"

    mail.send(msg)

    return redirect(url_for('emailsuccessdet'))

@app.route('/emailsuccess', methods=["GET", "POST"])
@login_required
def emailsuccess():
    if request.method == 'POST':
        return redirect(url_for('order'))
    return render_template('emailsuccess.html')

@app.route('/emailsuccesssumm', methods=["GET", "POST"])
@login_required
def emailsuccesssumm():
    if request.method == 'POST':
        return redirect(url_for('ordersummary'))
    return render_template('emailsuccesssumm.html')

@app.route('/emailsuccessdet', methods=["GET", "POST"])
@login_required
def emailsuccessdet():
    if request.method == 'POST':
        return redirect(url_for('orderdetail'))
    return render_template('emailsuccessdet.html')

@app.route('/test', methods=["GET"])
def test():
    return render_template('test.html')
