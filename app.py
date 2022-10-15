from flask import Flask, render_template, request, redirect, abort, url_for, make_response, flash
from os import urandom
from bson.objectid import ObjectId
import pymongo
import sys
import datetime

app = Flask(__name__)
app.secret_key = urandom(32)

# array of todo items
dummyData = [
    {
        'title': "Software Engineering Meeting",
        'content': "Meeting",
        'label': "Schoolwork",
        'Date': "10/16/2022",
        'Time': "4:00 pm",
        'Author': "User"
    },
    {
        'title': "Biology paper",
        'content': "Paper on prevalence of disease",
        'label': "Schoolwork",
        'Date': "10/16/2022",
        'Time': "12:00 pm",
        'Author': "User"
    },  
    {
        'title': "Tennis game",
        'content': "At astoria park",
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
        if bool(request.args["username"]) and bool(request.args["password"]):
            userInput = request.args["username"]
            passwordInput = request.args["password"]
            if (userInput == "demo" and passwordInput == "123"):
                return(redirect(url_for("homepage")))
            else:
                flash('Invalid login credentials.')
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
    if request.method == 'POST':
        u = request.form['username']
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
    return render_template("homepage.html", dummyData=dummyData)

@app.route('/all')
def all():
    """
    Route for the view all page
    """
    return render_template("all.html")

@app.route('/add')
def add():
    """
    Route for the add todo page
    """
    return render_template("add.html")

@app.route('/search')
def search():
    """
    Route for the search page
    """
    return render_template("search.html")

@app.route('/logout')
def logout():
    """
    Route to logout
    """
    return(redirect(url_for("login")))

if __name__ == "__main__":
    app.run(debug = True)
