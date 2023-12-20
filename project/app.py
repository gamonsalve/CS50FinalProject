from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import inspect
from sqlalchemy.sql import text
from base64 import b64encode
from datetime import datetime
from fileinput import filename
import os
from helpers import login_required, convertToBLOB, db_execute
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
            date_time = datetime.fromtimestamp(row.datetime)
            date_time = date_time.strftime("%m/%d/%Y, %H:%M:%S")
            print(date_time)
            new = {"id":row.newsid, "text": row.news_text, "title":row.title, "image":image, "datetime":date_time}
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

@app.route("/gestion_nouvelles",methods=["GET","POST"])
@login_required
def manage_news():
    if request.method == "POST":
        # let's check if we want to delete or edit
        edit = request.form.get("edit")
        delete = request.form.get("delete")
        new_id = request.form.get("new_id")
        create = request.form.get("create")
        if edit=="Edit":
            # edit news, Let;s move to the other view with a form
            return redirect(url_for(".edit_news",new_id=new_id))
        elif create=="Create":
            return redirect("creer_nouvelle")
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

    elif request.method == "GET":
        with db_engine.connect() as con:
            rs=db_execute(con, "SELECT title,newsid,user,datetime FROM news",{})
            news_list=rs.all()
            return render_template("manage_news.html",news_list=news_list)

@app.route("/creer_nouvelle", methods=["GET","POST"])
@login_required
def create_news():
    if request.method == "GET":
        #render the form
        return render_template("create_news.html")
    elif request.method == "POST":  
        # check form fields
        image = request.files["image"]
        image.save(image.filename)
        filename= image.filename
        image = convertToBLOB(image.filename)
        title = request.form.get("title")
        content_text = request.form.get("content_text")

        if None in (title, content_text):
            flash("An error has occured","error")
            return redirect("/creer_nouvelle")
        if "" in (title, content_text):
            flash("An error has occured","error")
            return redirect("/creer_nouvelle") 
        # Let's save the new
        with db_engine.connect() as con:
            date_time = datetime.now()
            date_time = date_time.timestamp()
            db_execute(con,
                       "INSERT INTO news (title, news_text, image, datetime, user) VALUES (:title, :content_text, :image, :date_time, :user)",
                       {"title":title, "content_text":content_text, 
                        "image":image, "date_time":date_time, "user":session["user_id"]})
            con.commit()
            flash("New Successfully created","success")
            return redirect("/")

    

@app.route("/modifier_nouvelle", methods=["GET","POST"])
@login_required
def edit_news():
    if request.method == "POST":
        new_id=request.form.get("new_id")
        image = request.files["image"]
        image.save(image.filename)
        filename= image.filename
        image = convertToBLOB(image.filename)
        title = request.form.get("title")
        content_text = request.form.get("content_text")
        print(new_id, title, content_text)
        if None in (new_id, title, content_text):
            flash("An error has occurred","error")
            return redirect("/gestion_nouvelles")

        if "" in (new_id, title, content_text):
            flash("An error has occurred","error")
            return redirect("/gestion_nouvelles")
        # Everything is ok let's update the new
        # confirm that the news exists
        with db_engine.connect() as con:
            rs = db_execute(con, "SELECT * FROM news WHERE newsid=:new_id",{"new_id":new_id})
            rows = rs.all()
            if len(rows)==1:
                # the new exists let's modify it
                date_time = datetime.now()
                date_time = date_time.timestamp()
                print(date_time)
                db_execute(con, "UPDATE news SET title=:title, news_text=:content_text, image=:image, datetime=:date_time WHERE newsid=:new_id",
                           {"title": title, "image":image, "content_text":content_text, "date_time":date_time,"new_id":new_id })
                con.commit()
                os.remove(filename)
                flash("New Successfully updated","success")
                return redirect(url_for(".news",newsid=new_id))

    elif request.method == "GET":
        # 1. show the form with the fields already populated
        # 2. check data base
        new_id = request.args.get("new_id")
        with db_engine.connect() as con:
            rs = db_execute(con, "SELECT * FROM news WHERE newsid=:new_id",{"new_id":new_id})
            rows = rs.all()
            if len(rows)==1:
                title = rows[0].title
                content = rows[0].news_text
                image = b64encode(rows[0].image).decode("utf-8")
            return render_template("edit_news.html",title=title, content=content, image=image, new_id=new_id)
    return redirect("/")


@app.route("/equipe")
def team():
    return render_template("team.html")

@app.route("/login",methods = ['POST', 'GET'])
def login():
    if session.get("user_id"):
        # redirect user to home page
        return redirect("/")
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
            else:
                flash("User not found","error")
                return redirect("/login")
            if valid_password:
                # Save session
                session["user_id"]=rows[0].username
                session["name"]= rows[0].name
                print(session["user_id"])
                return redirect("/")
            else:
                flash("incorrect password","error")
                return redirect("/login")
    # log user in
    elif request.method == "GET":
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
    elif request.method == "GET":
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