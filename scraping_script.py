from datetime import datetime
import time
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
from flask import Flask, json, jsonify, send_file
import os
import html
from urllib.parse import urlparse
from flask_cors import CORS

app = Flask(__name__)  # Initialize Flask application
CORS(app, resources={r"/api/*": {"origins": "*"}})


# Load configuration from YAML file
# Default to development config
config_file = os.getenv('CONFIG_FILE', 'config_dev.yaml')
# config_file = os.getenv('CONFIG_FILE', 'config_docker.yaml')  # For docker config
with open(config_file, 'r') as config_file:
    config = yaml.safe_load(config_file)

# URL to scrape from configuration file
URL = config['urls']
chromedriver_path = config['chromedriver_path']
DOMAIN = config['domains']
teams_data = []  # This will store the teams data

response_cache = {}

# Cache file path
CACHE_FILE = 'response_cache.json'

# Load cache from file if it exists
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as cache_file:
        response_cache = json.load(cache_file)
class Team:
    def __init__(self, name, link):
        self.name = name
        self.link = link
        self.players = []
        self.logo = ""
        self.background = ""

    def __str__(self):
        return json.dumps({
            "name": self.name,
            "link": self.link,
            "players": [player.to_dict() for player in self.players],  # Convert players to dictionaries
            "logo": self.logo,
            "background": self.background
        }, indent=4)

    def to_dict(self):
        return {
            "name": self.name,
            "link": self.link,
            "players": [player.to_dict() for player in self.players],
            "logo": self.logo,
            "background": self.background
        }

# Define the Player class
class Player:
    def __init__(self, number, name, link, nationalities):
        self.number = number
        self.name = name
        self.profile_link = "https://www.transfermarkt.com" + link
        self.stat_link = self.profile_link.replace("profil", "leistungsdatendetails")
        self.transfer_link = self.profile_link.replace("profil", "transfers")
        self.award_link = self.profile_link.replace("profil", "erfolge")
        self.nationalities = nationalities
        self.awards = []
        self.club_history = []

        # Initialize optional attributes with default values
        self.full_name = ""
        self.DOB = ""
        self.age = ""
        self.height = ""
        self.foot = ""
        self.appearances = 0
        self.goals = 0
        self.minutes_played = 0
        self.image_url = ""
        self.position = ""

    def add_player_profile(self, full_name, DOB, age, height, foot):
        self.full_name = full_name
        self.DOB = DOB
        self.age = age
        self.height = height
        self.foot = foot

    def add_player_stats(self, appearances, goals, minutes_played):
        self.appearances = appearances
        self.goals = goals
        self.minutes_played = minutes_played

    def to_dict(self):
        return {
            "number": self.number,
            "name": self.name,
            "profile_link": self.profile_link,
            "stat_link": self.stat_link,
            "nationalities": self.nationalities,
            "full_name": self.full_name,
            "DOB": self.DOB + " (" + self.age + ")",
            "age": self.age,
            "height": self.height[:-2] if self.height else "",
            "foot": self.foot,
            "awards": self.awards,
            "appearances": self.appearances,
            "goals": self.goals,
            "minutes_played": self.minutes_played,
            "club_history": self.club_history,
            "position": self.position,
            "image_url": self.image_url,
        }
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
    # options.add_argument("--no-sandbox")  # Bypass OS security model for Docker
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")  # Disable GPU acceleration
    # options.add_argument("--disable-extensions")  # Disable extensions
def get_player_data(player, file_path='data.json'):
    """Extract player data using Selenium and regular expressions, saving and updating to a file."""

    # Load existing data from file
    existing_data = load_existing_data(file_path)
    
    # `existing_data` is a list, so find the team that contains this player
    team_index = None

    for index, team in enumerate(existing_data):
        # Check if player is in the team's player list
        if any(p["name"] == player.name for p in team.get("players", [])):
            team_index = index
            break

    if team_index is None:
        print(f"Player {player.name} not found in any team.")
        return  # Exit if player not found in any team

    # Reference to the team where the player is located
    team_data = existing_data[team_index]

    # Ensure that players is a dictionary in the team data
    if not isinstance(team_data.get("players", []), list):
        team_data["players"] = []

    # Check if the player already exists in the team's player list
    for existing_player in team_data["players"]:
        if existing_player["name"] == player.name:
            # Check if the image URL and position are already set
            if 'image_url' in existing_player and existing_player['image_url'] != "" and 'position' in existing_player and existing_player['position'] != "":
                print(f"Player {player.name} already has image URL and position. Skipping scraping.")
                player.image_url = existing_player['image_url']
                player.position = existing_player['position']
                return  # Skip further scraping since data is cached

    # Setup Selenium options for headless browsing
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off for headless mode
    options.add_argument("--disable-extensions")  # Disable extensions for performance
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Fetch player details using Selenium
        driver.get('https://www.premierleague.com/players')
        time.sleep(5)  # Wait for page to load

        # Wait for the search input to be clickable and then perform the search
        search_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "search-input"))
        )

        search_input.clear()
        search_input.send_keys(player.name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(5)  # Allow time for search results to load

        # Wait for search results to load and be visible
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "player"))
        )

        # Parse the resulting page source
        html_content = driver.page_source

        # Extract image URL and position using regex patterns
        pattern_image = r'<img[^>]*class="img player__name-image"[^>]*src="([^"]*)"'
        pattern_position = r'<td[^>]*class="u-hide-mobile-lg player__position"[^>]*>(.*?)<\/td>'

        # Use regex to find matches in the HTML content
        image_match = re.search(pattern_image, html_content)
        position_match = re.search(pattern_position, html_content)

        # Set extracted data to the player object
        player.image_url = image_match.group(1).replace("40x40", "250x250") if image_match else "N/A"
        player.position = position_match.group(1).strip() if position_match else "N/A"

        # Update the existing data dictionary with the player's information
        for existing_player in team_data["players"]:
            if existing_player["name"] == player.name:
                existing_player['image_url'] = player.image_url
                existing_player['position'] = player.position

        # Save updated data back to JSON file
        save_data(file_path, existing_data)

        print(f"Added Player: {player.name}, Position: {player.position}, Image URL: {player.image_url}")

    except Exception as e:
        print(f"Error fetching data for player {player.name}: {e}")

    finally:
        # Ensure the Selenium driver is properly closed
        driver.quit()

def load_existing_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # Return an empty dictionary if the file doesn't exist
    except json.JSONDecodeError:
        return {}  # Return empty dict if JSON is not properly formatted
    

def save_data(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def custom_request(url, selenium=False):
    """Custom request with caching"""
    # Check if URL is in cache
    if url in response_cache:
        print(f"Fetching data from cache for URL: {url}")
        return response_cache[url]

    if selenium:
        content = get_transfer_content(url)
    else:
        response = requests.get(url, headers=HEADERS)
        content = response.text if response.status_code == 200 else None

    # Store in cache and save to file
    if content:
        response_cache[url] = content
        save_cache()

    return content

def save_cache():
    """Save cache to a file."""
    with open(CACHE_FILE, 'w') as cache_file:
        json.dump(response_cache, cache_file, indent=4)


def get_player_details(player: Player):
    content = custom_request(player.profile_link)
    pattern = r'<div class="info-table[^>]*">(.*?)<\/div>'
    contents = re.findall(pattern, content, re.DOTALL)[0]
    span_pattern = r'<span[^>]*class="info-table__content[^>]*>(.*?)<\/span>'
    contents = re.findall(span_pattern, content, re.DOTALL)
    data_dict = {"full_name": player.name, "DOB": "14/09/1995",
                 "age": "29", "height": "180cm", "foot": "right"}
    for i in range(0, len(contents), 2):
        label = re.sub(r'<.*?>', '', contents[i]).replace('&nbsp;', '').strip()
        value = contents[i + 1] if i + 1 < len(contents) else None
        if value:
            cleaned_value = re.sub(r'<.*?>|&nbsp;|\n', '', value).strip()
            cleaned_value = re.sub(r'<img[^>]*>', '', cleaned_value).strip()
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value).strip()
            if label == "Date of birth/Age:":
                split_data = cleaned_value.split('(')
                date_part = split_data[0].strip()
                age_part = split_data[1].strip(")")
                date_object = datetime.strptime(date_part, '%b %d, %Y')
                formatted_date = date_object.strftime('%d/%m/%Y')
                cleaned_value = f"{formatted_date} {age_part}"
                data_dict["DOB"] = formatted_date
                data_dict["age"] = age_part
            elif label == "Height:":
                cleaned_value = cleaned_value.replace(
                    'm', 'cm').replace(',', '').strip()
                data_dict["height"] = cleaned_value
            elif label in ["Full name:", "Name in home country:"]:
                data_dict["full_name"] = cleaned_value
            elif label == "Foot:":
                data_dict["foot"] = cleaned_value

            # if label and cleaned_value:
            #      data_dict[label] = cleaned_value

    player.add_player_profile(data_dict["full_name"], data_dict["DOB"],
                              data_dict["age"], data_dict["height"], data_dict["foot"])


def get_player_awards(player: Player):
    html = custom_request(player.award_link)
    awards = []
    regex = r'<div class="row">(.*?)<div class="large-4'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'<h2 class="content-box-headline">(.*?)</h2>'
    html = re.findall(regex, html, re.DOTALL)
    for award in html:
        temp = award.strip().split('x ')
        temp = temp[1] + ' (' + temp[0] + ')'
        awards.append(temp)
    player.awards = awards


def get_player_stats(player : Player):
    appearances = 0
    goals_or_clean_sheet = 0
    minutes_played = 0

    html = custom_request(player.stat_link)
    regex = r'<div id="yw1"[^>]*>([\s\S]*?)</table>'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'(even|odd)">(.*?)(<tr class="|$)'
    html = re.findall(regex, html, re.DOTALL)
    for leage in html :
        leage = ''.join(leage)
        premier_leage_regex = r'title="Premier League" [^>]*>(.*?)</tr>'
        premier_leage = re.findall(premier_leage_regex, leage, re.DOTALL)
        if premier_leage :
            td_regex = r'<td.*?>(.*?)</td>'
            td = re.findall(td_regex, premier_leage[0], re.DOTALL)
            appearances_regex = r'<a.*?>(.*?)</a>'
            try:
                appearances += int(re.findall(appearances_regex, td[2], re.DOTALL)[0])
            except: 
                appearances += 0
            if player.position.lower() == 'goalkeeper':
                try:
                    goals_or_clean_sheet += int(td[6])
                except: 
                    goals_or_clean_sheet += 0
                    
                try:
                    minute = td[7]
                    minutes_played += int(''.join(re.findall(r'\d+', minute)))
                except: 
                    minutes_played += 0
            else :
                try:
                    goals_or_clean_sheet += int(td[3])
                except: 
                    goals_or_clean_sheet += 0
                    
                try:
                    minute = td[6]
                    minutes_played += int(''.join(re.findall(r'\d+', minute)))
                except: 
                    minutes_played += 0
    player.add_player_stats(appearances, goals_or_clean_sheet, minutes_played)
def get_player_club(player: Player):
    club_history_list = []
    transfer_year = str(datetime.now().year)
    regex = r'<div class="grid tm-player-transfer-history-grid".*?>(.*?)<a class='
    html = custom_request(player.transfer_link, True)
    html = re.findall(regex, html, re.DOTALL)
    for history in html:
        date_regex = r'<div class="grid__cell grid__cell--center tm-player-transfer-history-grid__date">(.*?)<\/div>'
        date = re.findall(date_regex, history, re.DOTALL)[0]
        club_regex = r'<div class="grid__cell grid__cell--center tm-player-transfer-history-grid__new-club">(.*?)<\/div>'
        club = re.findall(club_regex, history, re.DOTALL)[0]
        joined_regex = r'<*?class="tm-player-transfer-history-grid__club-link">(.*?)</(a|span)>'
        club = re.findall(joined_regex, club, re.DOTALL)[0][0]
        year = date.split(", ")[1]
        club_history = year + ' - ' + transfer_year + ' ' + club
        club_history_list.append(club_history)
        transfer_year = year
    player.club_history = club_history_list


def get_player_in_team(team: Team):
    html = custom_request(team.link)
    regex = r'<div id="yw1".*?>(.*?)</div>\s*?<a title="'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'<tbody*?>(.*?)</tbody>'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'(even|odd)">(.*?)(<tr class="|$)'
    players_html = re.findall(regex, html, re.DOTALL)
    title_regex = r'title="(.*?)"'
    link_regex = r'href="(.*?)"'
    nationality_regex = r'alt="(.*?)"'
    td_regex = r'<td.*?>(.*?)</td>'
    number_regex = r'rn_nummer>(.*?)</div>'
    for player_html in players_html:
        td = re.findall(td_regex, player_html[1], re.DOTALL)
        number = re.findall(number_regex, td[0], re.DOTALL)[0]
        name = re.findall(title_regex, td[1], re.DOTALL)[-1]
        nationalities = re.findall(nationality_regex, td[5], re.DOTALL)
        link = re.findall(link_regex, td[2], re.DOTALL)[0]
        # print(number, name, link, nationalities)
        team.players.append(Player(number, name, link, nationalities))


def get_transfer_content(url, max_retries=3, wait_time=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")

    driver_path = "C:\\Program Files\\ChromeDriver\\chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)

        for attempt in range(max_retries):
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.TAG_NAME, "iframe"))
                )

                driver.switch_to.frame(
                    driver.find_elements(By.TAG_NAME, "iframe")[1])
                break
            except Exception:
                print(
                    f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        accept_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[@title='Accept & continue']"))
        )
        accept_button.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'tm-transfer-history'))
        )
        transfer_history_element = driver.find_element(
            By.CLASS_NAME, 'tm-transfer-history')
        driver.execute_script(
            "arguments[0].scrollIntoView();", transfer_history_element)

        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, 'tm-player-transfer-history-grid'))
        )

        return driver.page_source

    finally:
        driver.quit()


def get_all_teams():
    url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1"
    html = custom_request(url)
    regex = r'<div id="yw1".*?>(.*?)</div>\s*?<div class="table-footer">'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'(even|odd)">(.*?)(<tr class="|</tbody>)'
    teams_html = re.findall(regex, html, re.DOTALL)
    regex = r'<td.*?>(.*?)</td>'
    title_regex = r'title="(.*?)"'
    link_regex = r'href="(.*?)"'
    for team_html in teams_html:
        team = re.findall(regex, team_html[1], re.DOTALL)
        name = re.findall(title_regex, team[0], re.DOTALL)[
            0].replace("&amp;", "&")
        link = "https://www.transfermarkt.com/" + \
            re.findall(link_regex, team[0], re.DOTALL)[0]
        teams_data.append(Team(name, link))

def save_teams_to_data(file_path='data.json'):
    """Function to save all teams data and their players to a JSON file."""
    global teams_data  # Ensure we're using the global teams list
    get_all_teams()  # Fetch teams (if not already fetched)

    # Iterate through each team in the teams list with a progress bar
    for team in tqdm(teams_data, desc='Processing Teams', unit='team'):
        get_player_in_team(team)  # Populate the team's players

        # Save team data with updated players before fetching additional details
        save_data(file_path, [team.to_dict() for team in teams_data])

        # Iterate through each player in the team's players list with a progress bar
        for player in tqdm(team.players, desc=f'Processing Players in {team.name}', unit='player', leave=False):
            get_player_details(player)  # Get player's general details
            get_player_awards(player)   # Get player's awards (if any)
            get_player_club(player)     # Get player's club history (if needed)
            get_player_data(player)     # Get player's image URL and position using Selenium
            get_player_stats(player)
            # Save after updating each player to avoid losing data in case of failure
            save_data(file_path, [team.to_dict() for team in teams_data])

        print(f"Saved data for team: {team.name}")

if __name__ == '__main__':
    save_teams_to_data()  # Load teams data when starting the app
    app.run(host='0.0.0.0', port=5555)  # Start the Flask application