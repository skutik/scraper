from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    send_from_directory,
)
from src.mongo_interface import MongoInterface
import asyncio
from pymongo import errors
import logging
import os

mongo_client = MongoInterface(test_enviroment=True)
loop = asyncio.get_event_loop()

logging.getLogger().setLevel(logging.DEBUG)

"""
Test accounts

1#

id:"testovic1@email.com"
password:"Test1"
name:"testovic1"

2#

id:"testovic2@email.com"
password:"Test1"
name:"testovic1"

3#

id:"tes@mail.com"
password:"test"
name:"david"

"""


def insert_user(name, password, email):
    try:
        loop.run_until_complete(
            mongo_client.insert_user(name=name, password=password, email=email)
        )
    except errors.DuplicateKeyError:
        return f"Email {email} already exists. Try to login!"
    except Exception as e:
        return e
    else:
        return f"Email {email} registered sucessfully!"


def fetch_user(email):
    return loop.run_until_complete(mongo_client.fetch_user(email=email))


def fetch_filters():
    filters_list = loop.run_until_complete(mongo_client.fecth_filters())
    filters = dict()
    for filter_document in filters_list:
        filters[filter_document["_id"]] = [
            (key, value)
            for key, value in filter_document.items()
            if key not in ["_id", "last_update_utc"]
        ]
    return filters


def update_user_preferences(user_id, category, values):
    return loop.run_until_complete(
        mongo_client.upsert_user_preferences(
            email=user_id, filter_category=category, values=values
        )
    )


app = Flask("__name__")
app.secret_key = "NvTW%ac-c\a%5&AA8F6a"


@app.route("/")
def print_index_page():
    return "Vitejte na strance sReality sraperu."


@app.route("/favicon.ico")
def provide_favicon():
    print(app.root_path)
    return send_from_directory(os.path.join(app.root_path, "templates"), "favicon.ico")


@app.route("/register", methods=["GET", "POST"])
def post_registration_form():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        return insert_user(name=name, password=password, email=email)
    elif request.method == "GET":
        return render_template("register.html")
    else:
        return "Unsupported method!"


@app.route("/login", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        password = request.form["password"]
        email = request.form["email"]
        response = fetch_user(email=email)
        if not response or response["password"] != password:
            return "Login failed!"
        elif response["password"] == password:
            session["logged"] = True
            session["user_id"] = response["_id"]
            session["user_name"] = response["name"]
            session["filter_preferences"] = response.get("filter_preferences")
            return redirect("profile")
    elif request.method == "GET":
        if session.get("logged", False):
            return redirect("profile")
        return render_template("login.html")
    else:
        return "Unsupported method!"


@app.route("/logout", methods=["POST"])
def logout_user():
    if request.method == "POST":
        if not session.get("logged", False):
            return redirect("/login")
        session["logged"] = False
        session["user_id"] = None
        session["user_name"] = None
        session["filter_preferences"] = None
        return redirect("/")
    else:
        return "Unsupported method!"


@app.route("/profile", methods=["GET", "POST"])
def generate_profil_page():
    if request.method == "GET":
        filters = fetch_filters()
        if not session.get("logged", False):
            return redirect("login")
        logging.debug(fetch_user(session["user_id"]))
        session["filter_preferences"] = fetch_user(session["user_id"]).get(
            "filter_preferences"
        )
        return render_template(
            "profile.html",
            user_name=session["user_id"],
            main_category=filters["category_main_cb"],
            preferences=session["filter_preferences"].get("category_main_cb"),
        )
    else:
        return "Unsupported method!"


@app.route("/update_preferences", methods=["POST"])
def update_preferences():
    if request.method == "POST":
        logging.debug(request.form.getlist("category_main_cb"))
        result = update_user_preferences(
            session["user_id"],
            "category_main_cb",
            request.form.getlist("category_main_cb"),
        )
        logging.debug(result)
        return redirect("profile")
    else:
        return "Unsupported method!"
