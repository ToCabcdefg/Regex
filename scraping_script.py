import requests
from bs4 import BeautifulSoup
import re
import csv

# URL to scrape
URL = "https://www.capology.com/uk/premier-league/salaries/"

def fetch_html(url):
    """Fetch HTML content of the webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to retrieve the page. Status code: {response.status_code}")

def parse_html(html):
    """Parse the HTML content using BeautifulSoup and extract team data."""
    soup = BeautifulSoup(html, "html.parser")

    teams_html = soup.select("#panel > div.content-block > div > div.col.s12.team-row-container > div.col.s12.team-row")

    # Convert BeautifulSoup elements to a string for regex processing
    teams_html_str = "".join([str(div) for div in teams_html])

    # Use regex to extract team URL, image URL, and team name
    team_info = re.findall(
        r'<a href="(.*?)">\s*<div class="team-row-group team-row-group-test">\s*<img.*?src="(.*?)".*?>\s*<h6 class="team-history-text".*?>(.*?)</h6>',
        teams_html_str
    )

    # Create a list of dictionaries for the team information
    teams = [{'Team Name': name, 'URL': f"https://www.capology.com{url}", 'Image URL': img_url} for url, img_url, name in team_info]

    # Print the extracted information
    for team in teams:
        print(team)

    return teams

def save_to_csv(items, filename="./player.csv"):
    """Save team data to a CSV file."""
    # Convert list of dictionaries to list of lists for CSV writing
    rows = [[team['Team Name'], team['URL'], team['Image URL']] for team in items]

    # Open and write to CSV file
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["Team Name", "URL", "Image URL"])
        # Write data rows
        writer.writerows(rows)

    print(f"Data has been successfully saved to {filename}.")

def main():
    # Fetch the HTML content of the webpage
    html = fetch_html(URL)
    # Parse the HTML and extract team information
    items = parse_html(html)
    # Save the extracted information to CSV
    save_to_csv(items)

if __name__ == "__main__":
    main()
