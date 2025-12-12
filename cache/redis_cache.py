import json
from redis import Redis, DataError, ConnectionError


class RedisCache:
    def __init__(self, config: dict):
        self.config = config
        self.conn = self._connect()

    def _connect(self):
        try:
            conn = Redis(**self.config)
            return conn
        except ConnectionError as err:
            print("Redis connection error:", err)
            return None

    def set_value(self, name: str, value_dict: dict, ttl: float = 0):
        try:
            value_js = json.dumps(value_dict)
            self.conn.set(name, value_js)
            if ttl > 0:
                self.conn.expire(name, ttl)
            return True
        except DataError as err:
            print(err)
            return False

    def get_value(self, name):
        value_js = self.conn.get(name)
        if value_js:
            return json.loads(value_js)
        return None

    # Уменьшить счетчик доступных мест
    def decrement(self, key, field="count", amount=1):
        val = self.get_value(key)
        if val and val.get(field, 0) >= amount:
            val[field] -= amount
            self.set_value(key, val)
            return True
        return False

    # Увеличить счетчик (при отмене)
    def increment(self, key, field="count", amount=1):
        val = self.get_value(key)
        if val:
            val[field] += amount
            self.set_value(key, val)
            return True
        return False

    # Получить корзину пользователя
    def get_cart(self, user_id):
        key = f"user:{user_id}:cart"
        cart = self.get_value(key)
        return cart or []

    # Сохранить корзину пользователя
    def set_cart(self, user_id, cart, ttl=3600):
        key = f"user:{user_id}:cart"
        self.set_value(key, cart, ttl)
