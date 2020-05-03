import asyncio
from flask import Flask, request, jsonify
from src.mongo_interface import MongoInterface
import logging

logging.getLogger().setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
mi = MongoInterface(test_enviroment=True)
app = Flask("__name__")

def fetch_estate(estate_id):
    return loop.run_until_complete(mi.fetch_estate(estate_id))

def fetch_filters():
    filters_list = loop.run_until_complete(mi.fecth_filters())
    filters = dict()
    for filter_document in filters_list:
        filters[filter_document["_id"]] = [
            (key, value)
            for key, value in filter_document.items()
            if key not in ["_id", "last_update_utc"]
        ]
    return filters

def fetch_user(email):
    return loop.run_until_complete(
        mi.fetch_user(email=email)
    )

@app.route("/")
def index_page():
    return "Welcome to estates scraper!"

@app.route("/fetch_estate") #, methods=["GET"])
def get_estate():
    if request.method == "GET":
        estate_id = request.args.get("id", type=str)
        data = fetch_estate(estate_id)
        logging.debug(data)
        if data:
            return jsonify({"status": "ok", "estate_id": estate_id, "data": data}), 200
        else:
            return jsonify({"status": "failed", "estate_id": estate_id, "message": "No estate with provided id doesn't exist"}), 404
    else:
        return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405

@app.route("/fetch_filters")
def get_filters():
    if request.method == "GET":
        data = fetch_filters()
        logging.debug(data)
        if data:
            return jsonify({"status": "ok", "data": data}), 200
        else:
            return jsonify({"status": "failed", "message": "Data unavailable"}), 404
    else:
        return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405

@app.route("/fetch_user")
def get_user():
    if request.method == "GET":
        email = request.args.get("email", type=str)
        data = fetch_user(email)
        logging.debug(data)
        if data:
            return jsonify({"status": "ok", "data": data}), 200
        else:
            return jsonify({"status": "failed", "message": "User doesn't exist"}), 404
    else:
        return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405

@app.route("/query_estates")
def get_estate_by_query():
    if request.method == "GET":
        logging.debug(request.args)
        limit = request.args.get("limit", type=int)
        sort = request.args.get("sort", type=str)
        logging.debug(f"Limit: {limit}")
    return jsonify({"status": "ok"}), 200

@app.route("/upsert_property", methods=["POST"])
def upsert_property():
    pass
