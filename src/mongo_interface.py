from pymongo import errors
from datetime import datetime
from motor import motor_asyncio
import asyncio
import logging
from src.config import *


class MongoInterface:
    def __init__(self, test_enviroment=True):
        self.mongo_client = motor_asyncio.AsyncIOMotorClient(MONGODB_CONN_STRING)
        self.database = TEST_DATABALSE if test_enviroment else PRODUCTION_DATABASE
        self.estates_collection = ESTATE_COLLECTION
        self.users_collection = USERS_COLLECTION
        self.filters_collection = FILTERS_COLLECTION

    async def upsert_property(self, record_id, record):
        doc_id = record_id
        response = await self.mongo_client[self.database][
            self.estates_collection
        ].update_one(
            {"_id": doc_id},
            {
                "$setOnInsert": {
                    "created_at_utc": datetime.utcnow(),
                    "inserted_at_utc": datetime.utcnow(),
                },
                "$set": {**record, **{"last_update_utc": datetime.utcnow()}},
            },
            upsert=True,
        )
        print(response.raw_result)

    async def insert_user(self, email, password, name):
        user = await self.mongo_client[self.database][self.users_collection].insert_one(
            {
                "_id": email,
                "password": password,
                "name": name,
                "registered_at_utc": datetime.utcnow(),
            }
        )
        if not user:
            return "unknown_email"
        if user and user["password"] != password:
            return "wrong_password"
        else:
            "ok"

    async def fetch_user(self, email):
        user_data = await self.mongo_client[self.database][self.users_collection].find_one(
            {"_id": email}
        )
        if user_data:
            del user_data["password"]
        return user_data

    async def upsert_filters(self, filters_dict):
        for key, values in filters_dict.items():
            response = await self.mongo_client[self.database][
                self.filters_collection
            ].update_one(
                {"_id": key},
                {"$set": {**values, **{"last_update_utc": datetime.utcnow()}}},
                upsert=True,
            )
            logging.info(f"{key} response: {response}")

    def fecth_filters(self):
        # return all documents for collection
        return (
            self.mongo_client[self.database][self.filters_collection]
            .find({})
            .to_list(None)
        )

    async def fetch_estate(self, document_id):
        return await self.mongo_client[self.database][self.estates_collection].find_one({"_id": document_id})

    async def query_estates(self, query):
        pass

    async def upsert_user_preferences(self, email, filter_category, values):
        # logging.debug(email)
        # logging.debug(filter_category)
        # logging.debug(values)
        filters = await self.mongo_client[self.database][self.filters_collection].find_one(
            {"_id": filter_category}
        )
        print(filters)
        response = await self.mongo_client[self.database][
            self.users_collection
        ].update_one(
            {"_id": email},
            {
                "$setOnInsert": {
                    "created_at_utc": datetime.utcnow(),
                    "inserted_at_utc": datetime.utcnow(),
                },
                "$set": {"filter_preferences": 
                    {filter_category: [filters.get(filter) for filter in values]}, 
                    **{"last_update_utc": datetime.utcnow()}},
            },
            upsert=True,
        )
        return response.raw_result

    def close(self):
        self.mongo_client.close()


# if __name__ == "__main__":
#     mi = MongoInterface(test_enviroment=True)
#     loop = asyncio.get_event_loop()
#     filters = loop.run_until_complete(mi.fecth_filters())
#     for flt in filters:
#         logging.debug(flt)
#     name = "testovic2",
#     password = "Test1",
#     email = "testovic1@email.com"
#     response = loop.run_until_complete(mi.fetch_user(password=password,
#                                                       email=email))
#     except errors.DuplicateKeyError:
#         print(f"Email {email} already exists. Try to login!")
#     except Exception as e:
#         print(e)
#     else:
#         print(f"Email {email} registered sucessfully! {response}")

# if __name__ == "__main__":
#     test_dict = {'available': True,
#                  'lon': 14.4444256,
#                  'lat': 50.0864868,
#                  'price_czk': 10500,
#                  'price_czk_unit': 'za měsíc',
#                  'category_main_cb': 1,
#                  'category_sub_cb': 47,
#                  'category_type_cb': 2,
#                  'seo_locality': 'praha-zizkov-rehorova',
#                  'locality': 'Řehořova, Praha 3 - Žižkov',
#                  'seller_id': 66815, 'phone': ['+420774810646'],
#                  'seller_name': None,
#                  'email': None,
#                  'Total price': '10\xa0500',
#                  'Total price_currency': 'Kč',
#                  'Total price_unit': 'za měsíc',
#                  'Poznámka k ceně': '+ utilities 1500CZK',
#                  'Order ID': '70957',
#                  'Update': 'Dnes',
#                  'Building': 'Smíšená',
#                  'Property status': 'Po rekonstrukci',
#                  'Ownership': 'Osobní',
#                  'Floor': '3. podlaží z celkem 9',
#                  'Usable area': '10',
#                  'Usable area_unit': 'm2',
#                  'Floorage': '10',
#                  'Floorage_unit': 'm2',
#                  'Gas': ['Plynovod'],
#                  'Waste': ['Veřejná kanalizace'],
#                  'Energy Performance Rating': 'Třída C - Úsporná',
#                  'Furnished': True}
#
    # client = MongoInterface(test_enviroment=True)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(client.upsert_user_preferences("testovic1@email.com",
    #     "category_main_cb",
    #     ["Domy"]))
    # loop.run_until_complete(client.test_find())
    # loop.run_until_complete(client.upsert_property(123456, test_dict))
