from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/nouvelles")
def news():
    return render_template("news_viewer.html")

@app.route("/equipe")
def team():
    return render_template("team.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#### Helper Functions #####
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function