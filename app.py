from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import requests
from util import playerFromTransfer
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
    # Check if response is cached
    cached_response = cache.get(url)
    if cached_response:
        return cached_response
    return None

def cache_response(url, response):
    # Store the response in Redis
    cache.set(url, response, timeout=30000)  # Cache for 300 seconds

def get_players(data):
    players = []
    for i in range(1, 100):
        url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?Spieler_page={i}&query={data}"
        
        # Try to get cached response
        cached_html_content = get_cached_response(url)
        
        if cached_html_content is None:
            # Fetch from Transfermarkt if not cached
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                cached_html_content = response.text
                # Cache the response
                cache_response(url, cached_html_content)
        else:
            print(f"Cache hit for URL: {url}")  # Optional: log cache hits

        # Process the HTML content
        players += playerFromTransfer(cached_html_content)

    return players

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.get('data')
    players = get_players(data.lower())

    # Convert players to a list of dictionaries for JSON serialization
    players_dict = [player.to_dict() for player in players]

    return jsonify(players_dict)

if __name__ == '__main__':
    app.run(debug=True)
