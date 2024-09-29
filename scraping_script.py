import requests
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tqdm import tqdm  # Import tqdm for progress display
import yaml
from flask import Flask, jsonify , send_file
import os

app = Flask(__name__)  # Initialize Flask application

# Load configuration from YAML file
with open("config.yaml", 'r') as config_file:
    config = yaml.safe_load(config_file)

# URL to scrape from configuration file
URL = config['url']
chromedriver_path = config['chromedriver_path']
teams_data = []  # This will store the teams data


@app.route('/api/teams', methods=['GET'])
def get_teams():
    """API endpoint to get team data."""
    return jsonify(teams_data)  # Send teams data as JSON response

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
        raise Exception(f"Failed to retrieve the page. Status code: {
                        response.status_code}")


def get_team_data(html):
    """Extract team data using regular expressions."""
    teams_html = re.findall(
        r'<a href="([^"]+)">\s*<div class="team-row-group team-row-group-test">\s*<img.*?src="(.*?)".*?>\s*<h6 class="team-history-text".*?>(.*?)</h6>\s*</div>\s*</a>',
        html,
        re.DOTALL
    )

    # Create team entries
    teams = []
    for url, img_url, name in teams_html:
        teams.append({
            'Team Name': name.strip(),
            'URL': f"https://www.capology.com{url}",
            'Image URL': img_url.strip(),
            'Players': []  # Initialize an empty list for players
        })

    return teams


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


def get_player_data(teams):
    """Extract player data using regular expressions."""

    for team in tqdm(teams, desc="Fetching player data", unit="team"):
        team_url = team['URL']
        team_html = fetch_dynamic_html(team_url)

        if team_html:
            # Use regex to find the tbody section and extract all tr elements
            tbody_match = re.search(
                r'<tbody>(.*?)</tbody>', team_html, re.DOTALL)

            if tbody_match:
                tbody_content = tbody_match.group(
                    1)  # Get the content inside tbody

                # Find all player rows
                players_html = re.findall(
                    r'<tr.*?>(.*?)</tr>', tbody_content, re.DOTALL)

                players = []
                for player_html in players_html:
                    # Extract player name using regex
                    name_match = re.search(
                        r'<td class="name-column">.*?<a(.*?)>(.*?)</a>', player_html, re.DOTALL)
                    if name_match:
                        player_url = re.search(
                            r'href="([^"]+)"', name_match.group(1).strip())
                        player_name = re.sub(
                            r'<.*?>', '', name_match.group(2)).strip()
                        url = f"https://www.capology.com{
                            player_url.group(1).strip()}"
                        players.append({"name": player_name, "url": url})
                team['Players'] = players
            else:
                print(f"No <tbody> found for team: {team['Team Name']}")

    return teams

def get_player_information_data():
    return

def save_to_csv(data, filename, data_type):
    """Save team or player data to a CSV file."""
    if data_type == 'teams':
        # Format teams as a list of rows for CSV output
        rows = [[team['Team Name'], team['URL'], team['Image URL']] for team in data]
        header = ["Team Name", "URL", "Image URL"]
    elif data_type == 'players':
        player_rows = []
        for team in data:
            team_name = team['Team Name']  # Get the team name
            for player in team['Players']:
                # Associate each player with their team
                player_rows.append([team_name, player['name'], player['url']])
        rows = player_rows
        header = ["Team Name", "Player Name", "Player URL"]

    # Write the data to a CSV file
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"{data_type.capitalize()} data has been successfully saved to {filename}.")

def save_teams_to_data():
    """Function to save teams data for API."""
    global teams_data
    html = fetch_html(URL)
    teams_data = get_team_data(html)
    teams_data = get_player_data(teams_data)  # Fetch players data


if __name__ == '__main__':
    save_teams_to_data()  # Load teams data when starting the app
    app.run(port=5555)  # Start the Flask application
