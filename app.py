from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import requests
from util import *
from flask_caching import Cache


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': "redis://localhost:6379/0"})

@app.route('/')
def form():
    return render_template('form.html')

def get_cached_response(url):
    cached_response = cache.get(url)
    if cached_response:
        return cached_response
    return None

def cache_response(url, response, length=30000):
    cache.set(url, response, timeout=length)

def get_players(data, page=1, limit=10):
    players = []
    added_players = {}
    i = 1
    max_pagination = 1
    while (i<=max_pagination):
        url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?Spieler_page={i}&query={data}"
        cached_html_content = get_cached_response(url)
        
        if cached_html_content is None:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                cached_html_content = response.text
                cache_response(url, cached_html_content)

        processed_players = get_brief_player_details(cached_html_content)
        for player in processed_players:
            if player.link not in added_players.keys():
                added_players[player.link] = True
                players.append(player) 
        if len(players) >= page*limit:
            return players[limit*(page-1):limit*page]
        if i==1:
            max_pagination = get_max_pagination(cached_html_content)
        i+=1

    return players

@app.route('/players', methods=['GET'])
def submit():
    name = request.args.get('name', '').lower()  
    limit = int(request.args.get('limit', 10)) 
    page = int(request.args.get('page', 1))

    players = get_players(name, page, limit)
    players_dict = [player.to_dict() for player in players]
    response = jsonify(players_dict)
    
    return response
