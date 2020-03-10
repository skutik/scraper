import pymongo
from datetime import datetime
from src.config import MONGODB_CONN_STRING
from motor import motor_asyncio
import asyncio

class MongoInterface():

    def __init__(self, database, collection):
        self.mongo_client = motor_asyncio.AsyncIOMotorClient(MONGODB_CONN_STRING)
        self.database = database
        self.collection = collection

    async def upsert_property(self, record_id, record):
        doc_id = record_id
        x = await self.mongo_client[self.database][self.collection].update_one(
            {"_id": doc_id},
            {
                "$setOnInsert": {"created_at_utc": datetime.utcnow(), "inserted_at_utc": datetime.utcnow()},
                "$set": {**record, **{"last_update_utc": datetime.utcnow()}}
            },
            upsert=True)
        print(x.raw_result)

    async def test_find(self):
        document = await self.mongo_client[self.database][self.collection].find_one()
        print(document)

    def close(self):
        self.mongo_client.close()


if __name__ == "__main__":
    test_dict = {'available': True,
                 'lon': 14.4444256,
                 'lat': 50.0864868,
                 'price_czk': 10500,
                 'price_czk_unit': 'za měsíc',
                 'category_main_cb': 1,
                 'category_sub_cb': 47,
                 'category_type_cb': 2,
                 'seo_locality': 'praha-zizkov-rehorova',
                 'locality': 'Řehořova, Praha 3 - Žižkov',
                 'seller_id': 66815, 'phone': ['+420774810646'],
                 'seller_name': None,
                 'email': None,
                 'Total price': '10\xa0500',
                 'Total price_currency': 'Kč',
                 'Total price_unit': 'za měsíc',
                 'Poznámka k ceně': '+ utilities 1500CZK',
                 'Order ID': '70957',
                 'Update': 'Dnes',
                 'Building': 'Smíšená',
                 'Property status': 'Po rekonstrukci',
                 'Ownership': 'Osobní',
                 'Floor': '3. podlaží z celkem 9',
                 'Usable area': '10',
                 'Usable area_unit': 'm2',
                 'Floorage': '10',
                 'Floorage_unit': 'm2',
                 'Gas': ['Plynovod'],
                 'Waste': ['Veřejná kanalizace'],
                 'Energy Performance Rating': 'Třída C - Úsporná',
                 'Furnished': True}

    client = MongoInterface(database="test_db", collection="props")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.test_find())
    # loop.run_until_complete(client.upsert_property(123456, test_dict))
