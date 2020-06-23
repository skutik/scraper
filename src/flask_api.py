import asyncio
from flask import Flask, request, jsonify
from src.mongo_interface import MongoInterface
from src.api_exceptions import LimitError, MissingRequiredParams, SortingDefinitionError
import logging
from pymongo import ASCENDING, DESCENDING

logging.getLogger().setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
mi = MongoInterface(test_enviroment=True)
app = Flask("__name__")

app.config["TESTING"] = False

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

def fetch_estates(filter, projection, sort, limit):
    estates_list = loop.run_until_complete(mi.fetch_estates(filter, projection, sort, limit))
    if projection:
        return [estate.get("estate_url") for estate in estates_list]
    return estates_list


def fetch_user(email):
    return loop.run_until_complete(
        mi.fetch_user(email=email)
    )


@app.route("/")
def index_page():
    return "Welcome to estates scraper!"


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"ping": "pong"}), 200


@app.route("/fetch_estate", methods=["GET"])
def get_estate():
    estate_id = request.args.get("id", type=str)
    data = fetch_estate(estate_id)
    logging.debug(data)
    if data:
        return jsonify({"status": "success", "estate_id": estate_id, "data": data}), 200
    else:
        return jsonify({"status": "failed", "estate_id": estate_id, "message": "No estate with provided id doesn't exist"}), 404


@app.route("/fetch_filters", methods=["GET"])
def get_filters():
    data = fetch_filters()
    logging.debug(data)
    if data:
        return jsonify({"status": "success", "data": data}), 200
    else:
        return jsonify({"status": "failed", "message": "Data unavailable"}), 404


@app.route("/fetch_user", methods=["GET"])
def get_user():
    email = request.args.get("email", type=str)
    data = fetch_user(email)
    logging.debug(data)
    if data:
        return jsonify({"status": "success", "data": data}), 200
    else:
        return jsonify({"status": "failed", "message": "User doesn't exist"}), 404


@app.route("/query_estates", methods=["GET"])
def get_estate_by_query():

    def query_db(request_args):

        filter_query = dict()

        # Number of max returned estates (Limit is 100 estates per request)
        limit = request_args.get("limit", default=10, type=int)
        if limit not in range(1, 101):
            raise LimitError(f"Provided limit value '{limit}' is not allowed")

        # Type of estate: Flat, House, Land
        estate_type = request_args.getlist("estate_type", type=int)
        # Agreement type: Sale, Lease, Auction
        estate_agr_type = request_args.getlist("estate_agr_type", type=int)
        if not estate_type or not estate_agr_type:
            raise MissingRequiredParams()

        filter_query["category_main_cb"] = {"$in": estate_type}
        filter_query["category_type_cb"] = {"$in": estate_agr_type}

        # If true, then provide only estates with in available state
        available_only = request_args.get("availability", default=True, type=bool)
        if available_only:
            filter_query["available"] = True

        # Min. usable area
        min_usable = request_args.get("min_usable", default=0, type=int)
        filter_query["usable_area"] = {"$gte": min_usable}

        # Max price: For whole estate or monthly rent in the case of lease, default 1 for skipping estates with
        # unknown price
        price_limit = request_args.get("price_limit", default=None, type=int)
        if price_limit:
            filter_query["price_czk"] = {"$lte": price_limit}

        # Estate category: Could be flat proportion (3 + 1, 4 + kk, ..,), house for living, cottage, ...
        estate_category = request_args.get("estate_category", type=int)
        if estate_category:
            filter_query["category_sub_cb"] = {"$in": [estate_category]}

        # Please note that values for region and district can overlap since both values are connected with OR operator.
        # Therefore if user specifis whole region (e.g. region A) there is no need to explicitly specify also distrinc
        # from selected region because region will be already contained within results.
        # On the other hand, if user specifies whole region and also specify district outside of the selected region
        # then will be returned estates for whole region + extra district.

        # Region ID (Only Czech Rep.)
        region = request_args.get("region", type=int)
        if region:
            filter_query[""] = {"$in": region}

        # District ID (Only Czech Rep.)
        district = request_args.get("district", type=int)
        if district:
            filter_query["locality_district_id"] = {"$in": district}

        # Parameter tells if whole estate object should be returned or just list of estates URLs
        url_only = request_args.get("url_only", default=None, type=str)
        logging.debug(type(url_only))
        # if not url_only or url_only.lower() in ["0", "false", "f"]:
        url_only = {"estate_url": 1, "_id": 0} if url_only and url_only.lower() in ["0", "false", "f"] else None

        # Sorting attribute (e.g. price - then will be returned top x results with the lowest price)
        sort_keys = request.args.getlist("sort", type=str)
        sort_types = request_args.getlist("sort_type", type=int)
        if len(sort_keys) < len(sort_types):
            raise SortingDefinitionError()

        # Extend length with default values (ASCENDING sort) to be equal to 'sort_keys' list
        sort_types.extend([1] * (len(sort_keys) - len(sort_types)))
        # sort_types = [DESCENDING if sort_type == -1 else ASCENDING for sort_type in sort_types]
        # sorting = {"$sort": {key: sorting for key, sorting in zip(sort_keys, sort_types)}}
        sorting = [(sort_key, DESCENDING if sort_type == -1 else ASCENDING) for sort_key, sort_type in zip(sort_keys, sort_types)]

        logging.debug(filter_query)

        return fetch_estates(filter=filter_query, projection=url_only, sort=sorting, limit=limit)

    try:
        data = query_db(request.args)
    except LimitError:
        return jsonify({"status": "failed", "message": "Out of the Allowed Limit or Wrong Value"}), 400
    except MissingRequiredParams:
        return jsonify({"status": "failed", "message": "Missing One or More Required Params"}), 400
    except SortingDefinitionError:
        return jsonify({"status": "failed", "message": "Sorting Params Contains More Sorting Types Then Keys"}), 400
    # except Exception:
    #     return jsonify({"status": "failed", "message": "Unknown Error"}), 400
    else:
        return jsonify({"status": "success", "data": data}), 200

@app.route("/upsert_property", methods=["POST"])
def upsert_property():
    pass

@app.errorhandler(405)
def method_not_allowed(*_):
    return jsonify({"status": "failed", "message": "Method Not Allowed"}), 405
