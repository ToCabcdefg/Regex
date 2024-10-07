import re
import requests
import csv

base_url = "https://www.spotrac.com/epl/"

response = requests.get(base_url)
html_content = response.text

pattern = r"onClick=\"javascript: document\.location='epl/([^/]+)/epl'\""

teams = re.findall(pattern, html_content)
# print(teams)

def get_wage(team_url):
  response = requests.get(base_url + team_url + '/cap/_/year/2024')
  html_content = response.text
  pattern = re.compile(r'<a href="https://www.spotrac.com/epl/player/[^"]*"[^>]*>([^<]+)</a>.*?<td class=" text-center"[^>]*>\s*<span[^>]*>([^<]+)</span>', re.DOTALL)

  matches = pattern.findall(html_content)
  # print(matches)
  players_data=[]
  for match in matches:
    player_name = match[0].strip()
    wage = match[1].strip()
    players_data.append((player_name, wage))
  return players_data

premier_league_players = []
for team_url in teams:
  players_data = get_wage(team_url)
  if players_data:
        premier_league_players.extend(players_data)
        print(players_data)
  
# with open('premier_league_players.csv', mode='w', newline='', encoding='utf-8') as file:
#     writer = csv.writer(file)
#     writer.writerow(["Name", "Weekly Wage"])

#     for player_wage in premier_league_players:
#         writer.writerow(player_wage)