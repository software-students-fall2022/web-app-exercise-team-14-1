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
dummyData = [
    {
        'title': "Software Engineering Meeting",
        'details': "Meeting",
        'label': "Schoolwork",
        'Date': "10/16/2022",
        'Time': "4:00 pm",
        'Author': "User"
    },
    {
        'title': "Biology paper",
        'details': "Paper on prevalence of disease",
        'label': "Schoolwork",
        'Date': "10/16/2022",
        'Time': "12:00 pm",
        'Author': "User"
    },
    {
        'title': "Tennis game",
        'details': "At astoria park",
        'label': "Hobby",
        'Date': "10/16/2022",
        'Time': "10:00 am",
        'Author': "User"
    },
]

@app.route('/')
def login():
    """
    Processes login and redirects accordingly if request was made
    Otherwise display login form
    """
    if (request.args):
        # add valid username and login checking here
        # current only has a placeholder
        if bool(request.args["email"]) and bool(request.args["password"]):
            emailInput = request.args["email"]
            passwordInput = request.args["password"]
            userPasswordDocs = db.user.find({"email" : emailInput}, {"password": 1})
            if (userPasswordDocs.explain().get("executionStats", {}).get("nReturned") == 1):
                    if (userPassword[0] != passwordInput):
                        flash('Invalid password.')
                        return(redirect(url_for("login")))
                    else:
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
        u = request.form['email']
        p = request.form['password']
        m = request.form['match']
        if not u or not p or not m:
            flash('Please fill all fields.')
        elif p != m:
            flash('Password does not match.')
        else:
            return redirect(url_for('login'))
    return render_template("register.html")


@app.route('/homepage')
def homepage():
    """
    Route for the homepage page
    """

    #use dummy data for now
    return render_template("homepage.html", dummyData=dummyData, user='demo')

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

# with mongodb, @app.route('/edit/<mongoid>')
@app.route('/edit')
def edit():
    """
    Route for the edit page
    TODO
    Ex: find query from example app:
    doc = db.exampleapp.find_one({"_id": ObjectId(mongoid)})
    then pass in doc to the render template
    return render_template("edit.html", page="Edit", doc=doc)
    """
    return render_template("edit.html", page="Edit")

# route to accept the form submission
@app.route('/edit/<mongoid>', methods=['POST'])
def edit_todo(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    # Ex from prof's example app

    # name = request.form['fname']
    # message = request.form['fmessage']

    # doc = {
    #     # "_id": ObjectId(mongoid),
    #     "name": name,
    #     "message": message,
    #     "created_at": datetime.datetime.utcnow()
    # }

    # db.exampleapp.update_one(
    #     {"_id": ObjectId(mongoid)}, # match criteria
    #     { "$set": doc }
    # )

    return redirect(url_for("homepage"))

@app.route('/logout')
def logout():
    """
    Route to logout
    """
    return(redirect(url_for("login")))

if __name__ == "__main__":
    app.run(debug = True)
