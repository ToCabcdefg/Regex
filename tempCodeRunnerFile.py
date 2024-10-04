app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': "redis://localhost:6379/0"})