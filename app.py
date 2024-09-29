from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import requests
from util import getMaxPagination, playerFromTransfer
from flask_caching import Cache

HEADERS = {
    "Host": "www.transfermarkt.com",
    "Sec-Ch-Ua": '"Not;A=Brand";v="24", "Chromium";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, v=537.36)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=0, i",
    "Connection": "keep-alive"
}

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

def get_players(data):
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

        processed_players = playerFromTransfer(cached_html_content)
        for player in processed_players:
            if player.link not in added_players.keys():
                added_players[player.link] = True
                players.append(player) 
        
        if i==1:
            max_pagination = getMaxPagination(cached_html_content)
        i+=1

    return players

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.get('data').lower()
    input_path = "/submit/"+data
    cached_html_content = get_cached_response(input_path)
    if cached_html_content is not None:
        return cached_html_content
    
    players = get_players(data)
    players_dict = [player.to_dict() for player in players]
    response = jsonify(players_dict)
    cache_response(input_path, response, 30)
    
    return response
