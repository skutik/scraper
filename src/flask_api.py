import asyncio
from flask import Flask, request, jsonify
from src.mongo_interface import MongoInterface
import logging

logging.getLogger().setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
mi = MongoInterface(test_enviroment=True)
app = Flask("__name__")

MAX_LIMIT = 100

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

def query_estate_collection():
    pass

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
            return jsonify({"status": "success", "estate_id": estate_id, "data": data}), 200
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
            return jsonify({"status": "success", "data": data}), 200
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
            return jsonify({"status": "success", "data": data}), 200
        else:
            return jsonify({"status": "failed", "message": "User doesn't exist"}), 404
    else:
        return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405

@app.route("/query_estates")
def get_estate_by_query():
    if request.method == "GET":
        logging.debug(request.args)
        logging.debug(type(request.args))
        availability = request.args.get("availability", default=True, type=bool)
        min_floorage = request.args.get("min_floorage", default=0, type=int)
        price_limit = request.args.get("price_limit", type=int)
        estate_type = request.args.get("estate_type", type=int)
        estate_agr_type = request.args.get("estate_agr_type", type=int)
        estate_category = request.args.get("estate_category", type=int)
        region = request.args.get("region", type=int)
        district = request.args.get("district", type=int)
        url_only = request.args.get("url_only", True, type=bool)
        limit = request.args.get("limit", default=100, type=int)
        if limit > 100:
            return jsonify({"status": "failed", "message": "Not Allowed Limit, API Can Return Max 100 Results per Request"}), 401
        sort = request.args.get("sort", type=str)
        return jsonify({"status": "ok"}), 200
    else:
        return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405

@app.route("/upsert_property", methods=["POST"])
def upsert_property():
    pass
