from flask import Flask, render_template, request, redirect, abort, url_for, make_response, flash
from os import urandom
from bson.objectid import ObjectId
import pymongo
import sys
import datetime
from dotenv import dotenv_values

app = Flask(__name__)
app.secret_key = urandom(32)

config = dotenv_values(".env")

# connect to the database
cxn = pymongo.MongoClient(config['MONGO_URI'], serverSelectionTimeoutMS=5000)
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

# array of todo items
# dummyData = [
#     {
#         'title': "Software Engineering Meeting",
#         'details': "Meeting",
#         'label': "Schoolwork",
#         'Date': "10/16/2022",
#         'Time': "4:00 pm",
#         'Author': "User"
#     },
#     {
#         'title': "Biology paper",
#         'details': "Paper on prevalence of disease",
#         'label': "Schoolwork",
#         'Date': "10/16/2022",
#         'Time': "12:00 pm",
#         'Author': "User"
#     },
#     {
#         'title': "Tennis game",
#         'details': "At astoria park",
#         'label': "Hobby",
#         'Date': "10/16/2022",
#         'Time': "10:00 am",
#         'Author': "User"
#     },
# ]

#for storing the user information after logging in
username = {}

@app.route('/')
def login():
    """
    Processes login and redirects accordingly if request was made
    Otherwise display login form
    """
    if (request.args):
        if bool(request.args["email"]) and bool(request.args["password"]):
            emailInput = request.args["email"]
            passwordInput = request.args["password"]
            userPasswordDocs = db.user.find({"email" : emailInput}, {"password": 1})
            #doc = db.users.find_one({'email': emailInput})
            # may need to change this with new login system
            doc = db.users.find_one({"email": emailInput})
            # save the user ObjectID in the username dict for later use
            username['user_id'] = doc['_id']
            if (userPasswordDocs.explain().get("executionStats", {}).get("nReturned") == 1):
                    if (userPasswordDocs.next()["password"] != passwordInput):
                        flash('Invalid password.')
                        return(redirect(url_for("login")))
                    else:
                        # save the user's username in the username dict for later use
                        username['username'] = emailInput.split("@")[0]
                        return(redirect(url_for("homepage")))
            else:
                flash('No user found for email.')
                return(redirect(url_for("login")))
        else:
            flash('Please enter an email and password.')
            return(redirect(url_for("login")))
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route for the register page
    """
    if request.method == 'POST':
        e = request.form['email']
        p = request.form['password']
        m = request.form['match']
        userWithEmail = db.user.find({"email" : e})
        if not e or not p or not m:
            flash('Please fill all fields.')
        elif userWithEmail.explain().get("executionStats", {}).get("nReturned") > 0:
            flash('An account was already created for this email.')
        elif p != m:
            flash('Password does not match.')
        else:
            db.user.insert_one({"email": e, "password": p})
            return redirect(url_for('login'))
    return render_template("register.html")


@app.route('/homepage')
def homepage():
    """
    Route for the homepage page
    """
    # find the todos array using the logged in user's ObjectId
    todos = db.users.find_one({'_id': ObjectId(username['user_id'])}, {'todos': 1})['todos']
    # find the today todos
    today = datetime.date.today()
    date = today.strftime('%m/%d/%Y')
    # get today's todos in a list
    todayTodos = list(db.tasks.find({
        '_id': {
            '$in': todos
        },
        'date': date,
    }))
    # pass in today todos and the user's username to the homepage template
    return render_template("homepage.html",todos = todayTodos, user=username['username'])

@app.route('/all')
def all():
    """
    Route for the view all page
    """
    return render_template("all.html", page="View All")

@app.route('/add')
def add():
    """
    Route for the add todo page
    """
    return render_template("add.html", page="Add")

@app.route('/search')
def search():
    """
    Route for the search page
    """
    return render_template("search.html", page="Search")

@app.route('/edit/<todo_id>')
def edit(todo_id):
    """
    Route for the edit page
    """
    todo = db.tasks.find_one({'_id': ObjectId(todo_id)})
    return render_template("edit.html", page="Edit", doc=todo)

# route to accept the form submission
@app.route('/edit/<todo_id>', methods=['POST'])
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

    db.tasks.update_one(
        {'_id': ObjectId(todo_id)}, 
        {'$set': doc}
    )

    return redirect(url_for("homepage"))

# route to delete a specific post
@app.route('/delete/<todo_id>')
def delete(todo_id):
    """
    Route for GET requests to the delete page.
    """
    # db.tasks.delete_one({"_id": ObjectId(todo_id)})
    return redirect(url_for('homepage')) 

@app.route('/logout')
def logout():
    """
    Route to logout
    """
    #reset username dict
    username = {}
    print(username)
    return(redirect(url_for("login")))

if __name__ == "__main__":
    app.run(debug = True)
