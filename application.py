from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response, flash  # NOQA
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from appdb import Base, Category, Item, User
from flask import session as login_session
import random
import string
import json
import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
app = Flask(__name__)
engine = create_engine('sqlite:///app.db?check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# APPLICATION_NAME = "Item catalog"


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # NOQA
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except FlowExchangeError:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                  'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
# all category


@app.route('/')
@app.route('/catalog')
def allCategories():
    cat = session.query(Category)
    return render_template('all.html', cat=cat)
# details


@app.route('/catalog/<int:category_id>', methods=['GET', 'POST'])
def showitem(category_id):
    cats = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('categories.html', cats=cats, items=items)


@app.route('/catalog/<int:category_id>/add', methods=['GET', 'POST'])
def addi(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        addItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category_id,
                       user_id=login_session['user_id'])
        session.add(addItem)
        session.commit()
        flash("New item has been added")
        return redirect(url_for('showitem', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)


@app.route('/catalog/<int:category_id>/items/<int:itemid>/edit',
           methods=['GET', 'POST'])
def editi(category_id, itemid):
    items = session.query(Item).filter_by(id=itemid).one()
    if login_session['user_id'] != items.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit this founder.');}</script><body onload='myFunction()'>"  # NOQA
    if request.method == 'POST':
        if request.form['name']:
            items.name = request.form['name']
        if request.form['description']:
            items.description = request.form['description']
        return redirect(url_for('showitem', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
                               itemid=itemid, i=items)


@app.route('/catalog/<int:category_id>/items/<int:itemid>/delete',
           methods=['GET', 'POST'])
def deletei(category_id, itemid):
    if 'username' not in login_session:
        return redirect('/login')
    items = session.query(Item).filter_by(id=itemid).one()
    if login_session['user_id'] != items.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete this founder.');}</script><body onload='myFunction()'>"  # NOQA
    if request.method == 'POST':
        session.delete(items)
        session.commit()
        flash("item has been deleted")
        return redirect(url_for('showitem', category_id=category_id))
    else:
        return render_template('deletitem.html', i=items)


@app.route('/catalog/JSON')
def CategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


@app.route('/catalog/<int:catalog_id>/JSON')
@app.route('/catalog/<int:catalog_id>/items/JSON')
def CategoryJSON(catalog_id):
    categoryItems = session.query(Item).filter_by(category_id=catalog_id).all()
    return jsonify(categoryItems=[categoryItem.serialize
                   for categoryItem in categoryItems])


if __name__ == '__main__':
    app.secret_key = 'super_secure'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
