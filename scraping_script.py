import requests
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# URL to scrape
URL = "https://www.capology.com/uk/premier-league/salaries/"

def fetch_html(url):
    """Fetch HTML content of the webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content.decode('utf-8')  # Decode bytes to string
    else:
        raise Exception(f"Failed to retrieve the page. Status code: {response.status_code}")

def get_team_data(html):
    """Extract team data using regular expressions."""
    # Use regex to find all team links within the HTML
    teams_html = re.findall(
        r'<a href="(.*?)">\s*<div class="team-row-group team-row-group-test">\s*<img.*?src="(.*?)".*?>\s*<h6 class="team-history-text">(.*?)</h6>\s*</div>',
        html,
        re.DOTALL
    )

    # Create team entries
    teams = []
    for url, img_url, name in teams_html:
        teams.append({
            'Team Name': name.strip(),
            'URL': f"https://www.capology.com{url}",
            'Image URL': img_url.strip()
        })

    for team in teams:
        print(team)

    return teams

def fetch_dynamic_html(url):
    """Fetch dynamic HTML content using Selenium."""
    options = Options()
    # options.add_argument("--headless")  # Uncomment for headless mode
    service = Service(executable_path='/opt/homebrew/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#table > tbody"))
        )
        print(driver.page_source)  # Debug: check what is loaded
    except Exception as e:
        print(f"Error loading the page or finding the element: {e}")
        driver.quit()
        return None

    html = driver.page_source
    driver.quit()
    return html

def get_player_data(teams):
    """Extract player data using regular expressions."""
    
    for team in teams:
        team_url = team['URL']
        team_html = fetch_dynamic_html(team_url)
        if team_html:
            # Use regex to find all player rows in the HTML
            players_html = re.findall(r'<tr>(.*?)</tr>', team_html, re.DOTALL)
            
            players = []
            for player_html in players_html:
                # Extract player name using regex
                name_match = re.search(r'td.name-column > a.firstcol">(.*?)</a>', player_html, re.DOTALL)
                if name_match:
                    player_name = name_match.group(1).strip()
                    players.append(player_name)

            team['Players'] = players

    return teams

def save_to_csv(items, filename="./teams.csv"):
    """Save team data to a CSV file."""
    rows = [[team['Team Name'], team['URL'], team['Image URL'], team['Players']] for team in items]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Team Name", "URL", "Image URL", 'Players'])
        writer.writerows(rows)

    print(f"Data has been successfully saved to {filename}.")

def main():
    html = fetch_html(URL)
    teams = get_team_data(html)
    # teams = get_player_data(teams)
    # save_to_csv(teams)  # Uncomment if you want to save teams to CSV

if __name__ == "__main__":
    main()
