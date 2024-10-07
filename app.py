from flask import Flask, jsonify
from util import *
from cache_config import init_cache


app = Flask(__name__)
cache = init_cache(app)
init_data()

@app.route('/')
def form():
    return jsonify(get_all_players())
