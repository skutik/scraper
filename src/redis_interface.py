from redis import Redis
import json


class RedisInterface(object):
    def __init__(self, host, port=6379, password=None, db=0):
        self.redis = Redis(host=host, port=port, db=db, password=password)

    def get_dict(self, key) -> dict:
        str_dict = self.redis.get(key)
        return json.loads(str_dict)

    def store_dict(self, key, dict_to_store) -> None:
        str_dict = json.dumps(dict_to_store)
        self.redis.set(key, str_dict)
