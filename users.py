from flask import session, request, redirect, Blueprint, current_app
import flask_dance.contrib.google as oauth_google

from db import get_db

from pymysql.cursors import DictCursor

import bcrypt
import hashlib

user_api = Blueprint("users", __name__, url_prefix="/api/users")

# Setup OAuth
google_bp = oauth_google.make_google_blueprint(redirect_url="/api/users/auth/google/check", 
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile", 
        "https://www.googleapis.com/auth/userinfo.email", 
        "openid"
    ]
)
# Note, url_prefix overrides the entire user_api prefix, not sure if this will get changed
user_api.register_blueprint(google_bp, url_prefix="/api/users/auth")

@user_api.get("/auth/google/check")
def check_google_auth():
    resp = oauth_google.google.get("/oauth2/v1/userinfo")
    assert resp.ok, resp.text
    # TODO do something with google user id

    email = resp.json()["email"]
    query = "SELECT * from `users` WHERE `email`=%s"

    db = get_db()
    # Check if user exists, and either login or set session to create new account
    with get_db().cursor(cursor=DictCursor) as cursor:
        result = cursor.execute(query, (email))

        if (result == 0):
            session["pending_oauth_creation"] = email
        else:
            user = cursor.fetchone()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["admin"] = user["admin"] != 0



    return redirect("/profile")

    

@user_api.post("/create/oauth")
def create_user_oauth():
    """
    Example json input
    {
        "username" : "echoingsins"
    }
    """

    # We assume that the oauth srevice provides an email
    # TODO Save google account id?
    email = session["pending"]
    username = request.json["username"]

    # Validate username
    if (not valid_username(username)):
        return "Invalid username", 400

    query = "INSERT INTO `users` (`username`, `email`, `email_confirmed`) VALUES (%s, %s, %s)"

    db = get_db()
    with get_db().cursor() as cursor:
        result = cursor.execute(query, (username, email, True))

        if (result == 0):
            return ("User {} already exists".format(username), 409)

        db.commit()

    return ("User {} added".format(username), 201)


@user_api.post("/create")
def create_user():
    """
    Example json input
    {
        "username" : "echoingsins"
        "email" : "echoingsins@gmail.com    
        "password" : "lmao"
    }
    """

    if not all([field in request.json for field in ["username", "email", "password"]]):
        return "Invalid request", 400

    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"].encode() # TODO ensure charset is good

    # Validate username
    if (not valid_username(username)):
        return "Invalid username", 400

    # Use SHA256 to allow for arbitrary length passwords
    hash = bcrypt.hashpw(hashlib.sha256(password).digest(), bcrypt.gensalt())
    query = "INSERT INTO `users` (`username`, `hash`, `email`, `email_confirmed`) VALUES (%s, %s, %s, %s)"

    db = get_db()
    with get_db().cursor() as cursor:
        result = cursor.execute(query, (username, hash, email, False))

        if (result == 0):
            return ("User {} already exists".format(username), 409)

        db.commit()

    return ("User {} added".format(username), 201)


@user_api.post("/login")
def login():
    """
    Example json input
    {
        "username" : "echoingsins"
        "password" : "lmao"
    }

    OR 

    {
        "email" : "echoingsins@gmail.com"
        "password" : "lmao"
    }
    """

    # Validate request and pull fields
    if ("email" in request.json):
        query = "SELECT * FROM `users` WHERE `email`= %s"
        login = request.json["email"]
    elif ("username" in request.json):
        query = "SELECT * FROM `users` WHERE `username`= %s"
        login = request.json["username"]
    else:
        return ("Username/email not in request", 400)

    if ("password" not in request.json):
        return ("Password not in request", 400)
    
    password = request.json["password"].encode()

    db = get_db()
    with db.cursor(DictCursor) as cursor:
        # Query for user and check password
        result = cursor.execute(query, (login, ))

        if (result == 0):
            return "Bad username or password", 401

        user = cursor.fetchone()
        hash = user["hash"].encode()

        if not bcrypt.checkpw(hashlib.sha256(password).digest(), hash):
            return "Bad username or password", 401

    # Add session
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["admin"] = user["admin"] != 0

    return "Logged in", 200

@user_api.post("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("admin", None)
    return "Logged out", 200


def valid_username(username):
    valid_char = lambda c: (c.isalnum() or c == '-' or c == '_' or c == '.')
    return all(map(valid_char, username))