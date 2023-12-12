from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import inspect
from sqlalchemy.sql import text

app=Flask(__name__)

db_engine = create_engine("sqlite:///MQPST.db")
#metadata = MetaData()
#metadata.create_all(db_engine)

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/nouvelles")
def news():
    return render_template("news_viewer.html")

@app.route("/equipe")
def team():
    return render_template("team.html")

@app.route("/login",methods = ['POST', 'GET'])
def login():
    return render_template("login.html")

@app.route("/signup",methods = ['POST', 'GET'])
def signup():
    if request.method == 'POST':
        # 1. Let's get form data and confirm everything is ok
        username = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        print(name,username,password,confirmation)
        # no empty field
        if None in (name,username,password,confirmation):
            print("Empty field")
            return redirect("/signup")
        # matching passwords
        if password!=confirmation:
            print("Passwords do not match")
            return redirect("/signup")   
        # 2. Let's save the new user in the database
        with db_engine.connect() as con:
            rs = db_execute(con,"""INSERT INTO users (username,name,password) VALUES (:username,:name,:password)""",
                            {"username": username, "name":name,"password": password})
            con.commit() # commit to the DB
        # 3. let's redirect to login with a message.
        if success:
            return redirect("/")
        else:
            return redirect("/signup")  
    else:
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

def db_execute(db_connection,query,values):
    query = text(query)     
    return db_connection.execute(query,values)
