import requests
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm  # Import tqdm for progress display
import yaml
from flask import Flask, json, jsonify , send_file
import os
import html 
from urllib.parse import urlparse
from flask_cors import CORS

app = Flask(__name__)  # Initialize Flask application
CORS(app, resources={r"/api/*": {"origins": "*"}})


# Load configuration from YAML file
# config_file = os.getenv('CONFIG_FILE', 'config_dev.yaml')  # Default to development config
config_file = os.getenv('CONFIG_FILE', 'config_docker.yaml')  # For docker config
with open(config_file, 'r') as config_file:
    config = yaml.safe_load(config_file)

# URL to scrape from configuration file
URL = config['urls']
chromedriver_path = config['chromedriver_path']
DOMAIN = config['domains']
teams_data = []  # This will store the teams data


@app.route('/api/all', methods=['GET'])
def get_all():
    """API endpoint to get team data."""
    return jsonify(teams_data)  # Send teams data as JSON response

@app.route('/api/players', methods=['GET'])
def get_players():
    """API endpoint to get player data along with associated club information."""
    players = []
    for team in teams_data:
        team_name = team["club_name"]
        team_logo = team.get("club_logo_url", 'N/A')  # Use 'N/A' if no logo is found
        
        for player in team["players"]:
            players.append({
                "name": player["name"],
                "url": player["url"],
                "image_url": player.get("image_url", 'N/A'),  # Default to 'N/A' if missing
                "position": player.get("position", 'N/A'),  # Default to 'N/A' if missing
                "club": {  # Nested club object
                    "club_name": team_name,
                    "club_logo": team_logo
                }
            })
    return jsonify(players)

@app.route('/api/club/<team_name>', methods=['GET'])
def get_team_by_name(team_name):
    """API endpoint to get detailed information of a specific team by name."""
    # Find the team with the given name
    team = next((team for team in teams_data if team['club_name'].lower() == team_name.lower()), None)
    
    if team:
        # If the team is found, return the team details along with the players
        return jsonify({
            "club_name": team['club_name'],
            'team_logo': team.get("club_logo_url", 'N/A'),  # Return 'N/A' if no logo found
            "players": team["players"]  # Return the list of players for the team
        })
    else:
        # If the team is not found, return a 404 error
        return jsonify({"error": "Team not found"}), 404
    
@app.route('/api/teams', methods=['GET'])
def get_teams():
    """API endpoint to get team data."""
    teams = []
    for team in teams_data:
        teams.append({
            "club_name": team["club_name"],
            "club_logo": team.get("club_logo_url", 'N/A')  # Default to 'N/A' if no logo found
        })
    return jsonify(teams)

@app.route('/api/player/<player_name>', methods=['GET'])
def get_player_by_name(player_name):
    """API endpoint to get detailed information of a specific player by name."""
    player_data = []
    for team in teams_data:
        for player in team["players"]:
            if player["name"].lower() == player_name.lower():
                player_data.append({
                    "name": player["name"],
                    "url": player["url"],
                    "image_url": player.get("image_url", 'N/A'),  # Default to 'N/A' if missing
                    "position": player.get("position", 'N/A'),  # Default to 'N/A' if missing
                    "club": {  # Nested club object
                        "club_name": team["club_name"],
                        "club_logo": team.get("club_logo_url", 'N/A')  # Default to 'N/A' if no logo found
                    }
                })
    return jsonify(player_data)
    




@app.route('/api/teams/csv', methods=['GET'])
def download_teams_csv():
    """API endpoint to download the teams data as a CSV file."""
    csv_file_path = "teams.csv"
    if os.path.exists(csv_file_path):
        return send_file(csv_file_path, mimetype='text/csv', as_attachment=True)
    else:
        return jsonify({"error": "CSV file not found."}), 404



def fetch_html(url):
    """Fetch HTML content of the webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content.decode('utf-8')  # Decode bytes to string
    else:
        raise Exception(f"Failed to retrieve the page. Status code: {response.status_code}")


def fetch_dynamic_html(url):
    """Fetch dynamic HTML content using Selenium."""
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "#table > tbody"))
        )

    except Exception as e:
        print(f"Error loading the page or finding the element: {e}")
        driver.quit()
        return None

    html = driver.page_source
    driver.quit()
    return html


def is_valid_url(url):
    """Check if the URL is valid."""
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme) and bool(parsed_url.netloc)

def get_team_data(html_content,domain):
    """Extract team data using regular expressions."""
    # Updated regex to match the new HTML structure
    premier_league_section = re.search(
        r'<h2 class="[^"]*">Premier League</h2>(.*?)</div>',  # Match up until the closing div
        html_content,
        re.DOTALL
    )
    
    if premier_league_section:
        # Extract team names and URLs from the Premier League section
        teams_html = re.findall(
            r'<a href="([^"]+)">\s*<p class="Typography__Text-sc-1byk2c7-6 iXjxYl">(.*?)</p>\s*</a>',
            premier_league_section.group(1),
            re.DOTALL
        )

        # Create team entries
        teams = []
        for url, name in teams_html:
            # Decode the URL to handle any HTML entities (e.g., &amp; -> &)
            decoded_url = html.unescape(url.strip())
            full_url = f"{domain}{decoded_url}"

            # Check if the URL is valid before saving
            if is_valid_url(full_url) and name.strip() != "Highest Paid Players":
                teams.append({
                "club_name": name.strip(),
                "url": full_url,
                "players": []  # Initialize an empty list for players
            })
            else:
                print(f"Invalid URL for Team: {name.strip()}, URL: {full_url}")
            
            

        return teams
    
    return []

def get_player_data(teams, domain, file_path='team_data.json'):
    """Extract player data using Selenium and regular expressions, saving and updating to a file."""
    
    # Load existing data from file
    existing_data = load_existing_data(file_path)
    
    # Create a mapping from team name to team data for easy lookup
    existing_data_map = {team["club_name"]: team for team in existing_data}
    
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off for headless mode
    # Optional: For Docker environment
    options.binary_location = "/usr/bin/chromium"  # Path for Docker environment
    options.add_argument("--no-sandbox")  # Bypass OS security model for Docker
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--disable-extensions")  # Disable extensions
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    for team in tqdm(teams, desc="Fetching player data", unit="team"):
        team_url = team["url"]
        team_name = team["club_name"]
        team_html = fetch_html(team_url)

        # Retrieve existing team data or initialize a new entry
        if team_name in existing_data_map:
            team_data = existing_data_map[team_name]
        else:
            team_data = {
                "club_name": team_name,
                "url": team_url,
                "club_logo_url": "",
                "players": []
            }

        if team_html:
            # Extract and update team logo
            logo_match = re.search(r'<img[^>]*?src="([^"]+)"[^>]*?alt="[^"]*?logo"', team_html)
            if logo_match:
                team_logo_url = logo_match.group(1).strip().replace("league-logos", "club-logos")
                team_data["club_logo_url"] = team_logo_url
            else:
                print(f"No team logo found for team: {team_name}")

            # Extract player rows from tbody
            tbody_match = re.search(r'<tbody>(.*?)</tbody>', team_html, re.DOTALL)
            if tbody_match:
                tbody_content = tbody_match.group(1)
                players_html = re.findall(r'<tr.*?>(.*?)</tr>', tbody_content, re.DOTALL)

                for player_html in players_html:
                    # Extract player name and URL
                    name_match = re.search(
                        r'<td class="headcol"><a.*?href="([^"]+)".*?>(.*?)</a>',
                        player_html,
                        re.DOTALL
                    )

                    if name_match:
                        player_url = name_match.group(1).strip()
                        player_name = re.sub(r'<.*?>', '', name_match.group(2)).strip()
                        full_url = f"{domain}{player_url}"

                        # Validate URL
                        if not is_valid_url(full_url):
                            print(f"Invalid URL for player: {player_name}, URL: {full_url}")
                            continue

                        # Check if player already exists
                        existing_player = next(
                            (p for p in team_data["players"] if p["name"] == player_name),
                            None
                        )
                        if existing_player:
                            continue  # Skip existing players

                        # Fetch player details using Selenium
                        try:
                            driver.get('https://www.premierleague.com/players')

                            # Wait for the search input to be clickable
                            search_input = WebDriverWait(driver, 20).until(
                                EC.element_to_be_clickable((By.ID, "search-input"))
                            )

                            # Perform search
                            search_input.clear()
                            search_input.send_keys(player_name)
                            search_input.send_keys(Keys.RETURN)

                            # Wait for search results to load
                            WebDriverWait(driver, 20).until(
                                EC.visibility_of_element_located((By.CLASS_NAME, "player"))
                            )

                            # Parse the resulting page
                            html_content = driver.page_source

                            # Extract image URL and position
                            image_match = re.search(
                                r'<img[^>]*class="img player__name-image"[^>]*src="([^"]*)"',
                                html_content
                            )
                            position_match = re.search(
                                r'<td[^>]*class="u-hide-mobile-lg player__position"[^>]*>(.*?)<\/td>',
                                html_content
                            )

                            image_url = image_match.group(1).replace("40x40", "250x250") if image_match else "N/A"
                            position = position_match.group(1).strip() if position_match else "N/A"

                            # Append player data
                            team_data["players"].append({
                                "name": player_name,
                                "url": full_url,
                                "image_url": image_url,
                                "position": position
                            })

                            print(f"Added Player: {player_name}, Position: {position}, Image URL: {image_url}")

                        except Exception as e:
                            print(f"Error fetching data for player {player_name}: {e}")

            else:
                print(f"No <tbody> found for team: {team_name}")

        # Update the mapping
        existing_data_map[team_name] = team_data

    # Close the Selenium driver
    driver.quit()

    # Convert the mapping back to a list
    updated_data = list(existing_data_map.values())

    # Save updated data to the file
    save_data_to_file(updated_data, file_path)

    return updated_data

def load_existing_data(file_path):
    """Load existing team and player data from the file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_data_to_file(data, file_path):
    """Save updated data to the file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
        
def save_to_csv(data, filename, data_type):
    """Save team or player data to a CSV file."""
    if data_type == 'teams':
        # Format teams as a list of rows for CSV output
        rows = [[team["club_name"], team["url"], team['Image URL']] for team in data]
        header = ["club_name", "url", "Image URL"]
    elif data_type == "players":
        player_rows = []
        for team in data:
            team_name = team["club_name"]  # Get the team name
            for player in team["players"]:
                # Associate each player with their team
                player_rows.append([team_name, player["name"], player["url"]])
        rows = player_rows
        header = ["club_name", "Player Name", "Player URL"]

    # Write the data to a CSV file
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"{data_type.capitalize()} data has been successfully saved to {filename}.")

def save_teams_to_data():
    """Function to save teams data for API."""
    global teams_data
    salarysport_url = URL[0]
    salarysport_domain = DOMAIN[0]
    html = fetch_html(salarysport_url)
    teams_data = get_team_data(html,salarysport_domain)
    # save_to_csv(teams_data, "teams.csv", "teams")
    teams_data = get_player_data(teams_data,salarysport_domain)  # Fetch players data
    # save_to_csv(teams_data, "players.csv", "players")


if __name__ == '__main__':
    save_teams_to_data()  # Load teams data when starting the app
    app.run(host='0.0.0.0', port=5555)  # Start the Flask application
