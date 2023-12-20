import csv
import datetime
#import pytz
#import requests
import subprocess
import urllib
import uuid
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import inspect
from sqlalchemy.sql import text
from flask import redirect, render_template, session
from functools import wraps

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

def convertToBLOB(filename):
    with open(filename, "rb") as file:
        blob_data = file.read()
        return blob_data