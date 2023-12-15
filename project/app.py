from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import inspect
from sqlalchemy.sql import text
from base64 import b64encode
app=Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db_engine = create_engine("sqlite:///MQPST.db")
#metadata = MetaData()
#metadata.create_all(db_engine)

@app.route("/")
def index():
    with db_engine.connect() as con:
        rs=db_execute(con,"SELECT * FROM news LIMIT 3",{})
        rows=rs.all()
        news=[]
        for row in rows:
            #let's populate news list
            image = b64encode(row.image).decode("utf-8")
            new = {"id":row.newsid, "text": row.news_text, "title":row.title, "image":image, "datetime":row.datetime}
            news.append(new)
    return render_template("index.html",news=news)



@app.route("/nouvelles", methods = ["GET"])
def news():
    # get the new id from get
    news_id=request.args.get("newsid")
    with db_engine.connect() as con:
        rs = db_execute(con,"SELECT * FROM news WHERE newsid=:news_id",{"news_id":news_id})
        rows = rs.all()
        image = b64encode(rows[0].image).decode("utf-8")
    return render_template("news_viewer.html",text=rows[0].news_text, title=rows[0].title,image=image)

@app.route("/modifier_nouvelle")
def edit_news():
    return redirect("/")

@app.route("/gestion_nouvelles",methods=["GET","POST"])
def manage_news():
    if request.method == "POST":
        # let's check if we want to delete or edit
        edit = request.form.get("edit")
        delete = request.form.get("delete")
        new_id = request.form.get("new_id")
        if edit=="Edit":
            # edit news, Let;s move to the other view with a form
            redirect("/modifier_nouvelle?newsid=")
        elif delete=="Delete":
            # check if selected new exists
            with db_engine.connect() as con:
                rs = db_execute(con, "SELECT * FROM news WHERE newsid=:new_id",{"new_id":new_id})
                rows = rs.all()
                if len(rows) == 1:
                    #new id exist, procced to delete
                    rs = db_execute(con, "DELETE FROM news WHERE newsid=:new_id",{"new_id":new_id})
                    con.commit()
                flash("New succesfully deleted","success")
                return redirect("/gestion_nouvelles")
        else:
            flash("An error has occured","warning")
            return redirect("\gestion_nouvelles")

    else:
        with db_engine.connect() as con:
            rs=db_execute(con, "SELECT title,newsid,user,datetime FROM news",{})
            news_list=rs.all()
            return render_template("manage_news.html",news_list=news_list)

@app.route("/equipe")
def team():
    return render_template("team.html")

@app.route("/login",methods = ['POST', 'GET'])
def login():
    
    session.clear()

    if request.method == "POST":
        # 1. get form data
        email = request.form.get("email")
        password = request.form.get("password")
        valid_password = False
        if "" in (email, password):
            print("empty field")
            return redirect("/login")
        if None in (email,password):
            print("Field not found")
            return redirect("/login")
        # 2. check if the users exists
        with db_engine.connect() as con:
            rs = db_execute(con, "SELECT * FROM users WHERE username == :email",{"email":email})
            rows = rs.all()
            if len(rows) == 1:
                # user exists let's check password
                 # 3. check if password match
                valid_password=check_password_hash(rows[0].password, password)
            
            if valid_password:
                # Save session
                session["user_id"]=rows[0].username
                session["name"]= rows[0].name
                print(session["user_id"])
                return redirect("/")
    # log user in
    else:
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
        if "" in (name,username,password,confirmation):
            print("Empty field")
            flash("Please fill all fields","error")
            return redirect("/signup")
        # matching passwords
        if password!=confirmation:
            print("Passwords do not match")
            flash("Passwords do not match","error")
            return redirect("/signup")
        else:
            #passwords match let's encrypt
            password_hash = generate_password_hash(password)  
        # 2. Let's save the new user in the database
        with db_engine.connect() as con:
            rs = db_execute(con,"""INSERT INTO users (username,name,password) VALUES (:username,:name,:password)""",
                            {"username": username, "name":name,"password": password_hash})
            con.commit() # commit to the DB
        # 3. let's redirect to login with a message.
            flash("User Succesfully Created","success")
            return redirect("/login")
    else:
        return render_template("signup.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

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
