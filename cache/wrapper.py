from functools import wraps
from cache.redis_cache import RedisCache


def fetch_from_cache(cache_name: str, cache_config: dict):
	cache_conn = RedisCache(cache_config['redis'])
	ttl = cache_config['ttl']

	def decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			cached_value = cache_conn.get_value(cache_name)
			print('cached_value=', cached_value)
			if cached_value:
				return cached_value
			response = f(*args, **kwargs)
			print('response=', response)
			cache_conn.set_value(cache_name, response, ttl)
			return response
		return wrapper
	return decorator
