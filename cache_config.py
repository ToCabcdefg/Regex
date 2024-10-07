# cache_config.py
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': "redis://localhost:6379/0"})

def init_cache(app):
    cache.init_app(app)
    return cache
