from flask import Flask, render_template, request, redirect, abort, url_for, make_response, flash
from os import urandom
from bson.objectid import ObjectId
import pymongo
import sys
import datetime
from dotenv import dotenv_values
import certifi
import re

# modules useful for user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = urandom(32)

# set up flask-login for user authentication
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


config = dotenv_values(".env")

# connect to the database
cxn = pymongo.MongoClient(config['MONGO_URI'], serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
try:
    # verify the connection works by pinging the database
    cxn.admin.command('ping') # The ping command is cheap and does not require auth.
    db = cxn[config['MONGO_DBNAME']] # store a reference to the database
    print(' *', 'Connected to MongoDB!') # if we get here, the connection worked!
except Exception as e:
    # the ping command failed, so the connection is not available.
    # render_template('error.html', error=e) # render the edit template
    print(' *', "Failed to connect to MongoDB at", config['MONGO_URI'])
    print('Database connection error:', e) # debug


# a class to represent a user
class User(flask_login.UserMixin):
    # inheriting from the UserMixin class gives this blank class default implementations of the necessary methods that flask-login requires all User objects to have
    # see some discussion of this here: https://stackoverflow.com/questions/63231163/what-is-the-usermixin-in-flask
    def __init__(self, data):
        '''
        Constructor for User objects
        @param data: a dictionary containing the user's data pulled from the database
        '''
        self.id = data['_id'] # shortcut to the _id field
        self.data = data # all user data from the database is stored within the data field

def locate_user(user_id=None, username=None):
    '''
    Return a User object for the user with the given id or username, or None if no such user exists.
    @param user_id: the user_id of the user to locate
    @param username: the username address of the user to locate
    '''
    if user_id:
        # loop up by user_id
        criteria = {"_id": ObjectId(user_id)}
    else:
        # loop up by username
        criteria = {"username": username}
    doc = db.users.find_one(criteria) # find a user with the given criteria

    # if user exists in the database, create a User object and return it
    if doc:
        # return a user object representing this user
        user = User(doc)
        return user
    # else
    return None

@login_manager.user_loader
def user_loader(user_id):
    '''
    This function is called automatically by flask-login with every request the browser makes to the server.
    If there is an existing session, meaning the user has already logged in, then this function will return the logged-in user's data as a User object.
    @param user_id: the user_id of the user to load
    @return a User object if the user is logged-in, otherwise None
    '''
    return locate_user(user_id=user_id) # return a User object if a user with this user_id exists


# set up any context processors
# context processors allow us to make selected variables or functions available from within all templates

@app.context_processor
def inject_user():
    # make the currently-logged-in user, if any, available to all templates as 'user'
    return dict(user=flask_login.current_user)

@app.route('/')
def login():
    """
    Processes login and redirects accordingly if request was made
    Otherwise display login form
    """

    # if the current user is already signed in, there is no need to sign up, so redirect them
    if flask_login.current_user.is_authenticated:
        flash('You are already logged in, silly!') # flash can be used to pass a special message to the template we are about to render
        return redirect(url_for('homepage')) # tell the web browser to make a request for the / route (the home function)
    if (request.args):
        if bool(request.args["username"]) and bool(request.args["password"]):
            usernameInput = request.args["username"]
            passwordInput = request.args["password"]
            user = locate_user(username=usernameInput)
            if user:
                    if check_password_hash(user.data['password'], passwordInput):
                        flask_login.login_user(user)
                        return(redirect(url_for("homepage")))
                    else:
                        flash('Invalid password.')
                        return(redirect(url_for("login")))
            else:
                flash('No user found for username.')
                return(redirect(url_for("login")))
        else:
            flash('Please enter an username and password.')
            return(redirect(url_for("login")))
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route for the register page
    """
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        m = request.form['match']

        if not u or not p or not m:
            flash('Please fill all fields.')
        elif locate_user(username=u):
            flash('An account was already created with this username.')
        elif p != m:
            flash('Password does not match.')
        else:
            hashed_password = generate_password_hash(p)
            db.users.insert_one({"username": u, "password": hashed_password, "todos": []})
            return redirect(url_for('login'))
    else:
        if flask_login.current_user.is_authenticated:
            flash('You are already logged in, silly!')
            return redirect(url_for('homepage'))
    return render_template("register.html")


@app.route('/homepage')
@flask_login.login_required
def homepage():
    """
    Route for the homepage page
    """

    # find the todos array using the logged in user's ObjectId
    todos = flask_login.current_user.data['todos']

    # find the today todos
    today = datetime.date.today()
    date = today.strftime('%Y-%m-%d')
    # get today's todos in a list
    todayTodos = list(db.todos.find({
        '_id': {
            '$in': todos
        },
        'date': date,
    }).sort([('time', 1)]))
    

    # pass in today todos and the user's username to the homepage template
    return render_template("homepage.html", todos = todayTodos, homepage=True)

# create a filter that jinja will use to format the time in the html to look nicer
# used in homepage.html and all.html
@app.template_filter('time_format')
def time_format(value, format="%I:%M %p"):
    todo_time = datetime.datetime.strptime(value, '%H:%M').time()
    return todo_time.strftime(format)

# create a filter that jinja will use to format the date in the html to look nicer
# used in all.html
@app.template_filter('date_format')
def date_format(value, format="%m/%d/%Y"):
    todo_date = datetime.datetime.strptime(value, '%Y-%m-%d')
    return todo_date.strftime(format)


@app.route('/all')
@flask_login.login_required
def all():
    """
    Route for the view all page
    """
    # find the todos array using the logged in user's ObjectId
    todos = flask_login.current_user.data['todos']

    # get all todos in a list
    allTodos = list(db.todos.find({
        '_id': {
            '$in': todos
        },
    }).sort([('date', 1), ('time', 1)]))

    return render_template("all.html", todos = allTodos, page="View All")

@app.route('/add', methods=['GET','POST'])
@flask_login.login_required
def add():
    """
    Route for the add todo page
    Accepts form submission data for new todo and saves to database
    """

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        label = request.form['label']
        date = request.form['date']
        time = request.form['time']
        
        doc = {
            'title': title,
            'content': content,
            'label': label,
            'date': date,
            'time': time,
        }

        # insert task into db
        returned_doc = db.todos.insert_one(doc)
        db.users.find_one_and_update({'_id': flask_login.current_user.id}, { '$push' : {'todos' : returned_doc.inserted_id}})

        return redirect(url_for('homepage'))
    
    return render_template("add.html", page="Add")

@app.route('/search', methods=['GET','POST'])
@flask_login.login_required
def search():
    # POST route
    if request.method == 'POST':
        query = request.form['query']
        search_by = request.form['search-by']
        input_error = False

        # search criteria dict for searching todos
        criteria = {
            '_id': {'$in': flask_login.current_user.data['todos']}
        }

        # search info in database based on search by (label, title, date)
        if search_by == 'Label':
            criteria['label'] = {'$regex' : f'{query}', '$options' : 'i'}
        elif search_by == 'Title':
            criteria['title'] = {'$regex' : f'{query}', '$options' : 'i'}
        else:
            # date input must match YYYY-MM-DD
            if not re.search('^\d\d\d\d-\d\d-\d\d$', query):
                input_error = True
                error_msg = 'Please enter your date in the format (YYYY-MM-DD)'
            else:
                try:
                    datetime.datetime.strptime(query, '%Y-%m-%d')
                    criteria['date'] = query
                except:
                    input_error = True
                    error_msg = 'Please enter a correct date'

        # return to search page if query is incorrect
        if input_error:
            return render_template('search.html', page="Search", prefill = query, error=error_msg)

        results = list(db.todos.find(criteria))
        found = len(results) != 0

        return render_template('search_result.html', results = results, found = found)

    # GET route
    return render_template("search.html", page="Search")

# @app.route('/search-result/<type>/<query>', )
# def search_results():

#     return render_template('search_result.html')


@app.route('/edit/<todo_id>')
@flask_login.login_required
def edit(todo_id):
    """
    Route for the edit page
    """
    todo = db.todos.find_one({'_id': ObjectId(todo_id)})
    todo_date = todo['date']
    todo_time = todo['time']
    
    return render_template("edit.html", page="Edit", doc=todo, date=todo_date, time=todo_time)

# route to accept the form submission
@app.route('/edit/<todo_id>', methods=['POST'])
@flask_login.login_required
def edit_todo(todo_id):

    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """

    title = request.form['title']
    content = request.form['details']
    label = request.form['label']
    date = request.form['date']
    time = request.form['time']
    
    doc = {
        'title': title,
        'content': content,
        'label': label,
        'date': date,
        'time': time,
    }

    db.todos.update_one(
        {'_id': ObjectId(todo_id)},
        {'$set': doc}
    )

    return redirect(url_for("homepage"))


@app.route('/returnToLogin')
def returnToLogin():
    """
    Route to logout
    """
    return(redirect(url_for("login")))

# route to delete a specific post
@app.route('/delete/<todo_id>/<dest>')
def delete(todo_id, dest):
    """
    Route for GET requests to the delete page.
    """
    # delete todo item from todos collection
    db.todos.delete_one({"_id": ObjectId(todo_id)})

    # get index of todo item to delete
    id_index = list(flask_login.current_user.data['todos']).index(ObjectId(todo_id))

    # set element to none using unset operator
    db.users.update_one(
        {'_id': ObjectId(flask_login.current_user.id)},
        {'$unset': {f'todos.{id_index}': 1}}
    )

    # remove none elements in todos array of users collection
    db.users.update_one(
        {'_id': ObjectId(flask_login.current_user.id)},
        {'$pull': {'todos': None}}
    )
    return redirect(url_for(dest)) 


@app.route('/logout')
@flask_login.login_required
def logout():
    """
    Route to logout
    """
    flask_login.logout_user()
    return(redirect(url_for("login")))

if __name__ == "__main__":
    app.run(debug = True)
