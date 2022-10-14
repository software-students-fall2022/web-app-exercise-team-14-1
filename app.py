from flask import Flask, render_template, request, redirect, abort, url_for, make_response, flash
from os import urandom
from bson.objectid import ObjectId
import pymongo
import sys
import datetime

app = Flask(__name__)
app.secret_key = urandom(32)

@app.route('/')
def login():
    """
    Processes login and redirects accordingly if request was made
    Otherwise display login form
    """
    if (request.args):
        # add valid username and login checking here
        # current only has a placeholder
        if (bool(request.args["username"]) and bool(request.args["password"])):
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
    if (request.args):
        # add valid username and login checking here
        # current only has a placeholder
        if (bool(request.args["username"]) and bool(request.args["password"]) and bool(request.args["match"])):
            userInput = request.args["username"]
            passwordInput = request.args["password"]
            if (bool[request.args["username"]]): # PLACEHOLDER - Check that the username hasnt been used
                if (request.args["password"] == request.args["match"]):
                    return(redirect(url_for("homepage")))
                else:
                    flash('Password must match.')
                    return(redirect(url_for("register")))
            else:
                flash('Username has been taken.')
                return(redirect(url_for("register")))
        else:
            flash('Please enter all fields.')
            return(redirect(url_for("register")))
    else:
        return render_template("register.html")

@app.route('/homepage')
def homepage():
    """
    Route for the homepage page
    """
    return render_template("homepage.html")

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

@app.route('/logout')
def logout():
    """
    Route to logout
    """
    return(redirect(url_for("login")))

if __name__ == "__main__":
    app.run(debug = True)
