from   datetime import datetime
import re
import requests

class Team: 
    def __init__(self, name, link):
        self.name = name
        self.link = link
        self.players = []
        self.logo = ""
        self.background = ""
class Player:
    def __init__(self, number, name, link, nationalities):
        self.number = number
        self.name = name
        self.profile_link = "https://www.transfermarkt.com" +  link
        self.stat_link =  self.profile_link.replace("profil", "leistungsdatendetails")
        self.nationalities = nationalities
        
    def add_player_profile(self, full_name, DOB, age, height, foot):
        self.full_name = full_name
        self.DOB = DOB 
        self.age = age 
        self.height = height 
        self.foot = foot

    

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

teams = []

def get_max_pagination(html) -> int: 
    max_pagination = 1
    regex = r'<div class="row">(.*?)<div class="row"'

    try:
        html = re.findall(regex, html, re.DOTALL)[0]
    except IndexError:
        print("No rows found in the HTML.")
        return max_pagination
    regex = r'last-page.*?Spieler_page=(\d+)'
    try:
        html = re.findall(regex, html, re.DOTALL)[0]
        print(int(html))
        return int(html)
    except IndexError:
        print("No rows found in the HTML.")
        return max_pagination
    
def get_brief_player_details(html) -> list[Player]:
    players = []
    regex = r'<div class="row">(.*?)<div class="row"'
    
    try:
        html = re.findall(regex, html, re.DOTALL)[0]
    except IndexError:
        print("No rows found in the HTML.")
        return players
    
    regex = r'<table.*?>(.*)</table>'
    try:
        html = re.findall(regex, html, re.DOTALL)[0]
    except IndexError:
        print("No table found in the HTML.")
        return players
    
    regex = r'(even|odd)">(.*?)(<tr class="|</tbody>)'
    html = re.findall(regex, html, re.DOTALL)

    for player in html:
        regex = r'<td.*?>.*?</td>'
        temp = re.findall(regex, player[1], re.DOTALL)

        if len(temp) < 7:
            print("Insufficient data for player.")
            continue

        title_regex = r'title="(.*?)"'
        position_regex = r'>(.*?)<'
        link_regex = r'href="(.*?)"'
        
        try:
            link = "https://www.transfermarkt.com" + re.findall(link_regex, temp[1], re.DOTALL)[0]
            name = re.findall(title_regex, temp[1], re.DOTALL)[0]
            club = re.findall(title_regex, temp[2], re.DOTALL) or ['Retired']
            position = re.findall(position_regex, temp[3], re.DOTALL)[0]
            nationality = re.findall(title_regex, temp[6], re.DOTALL)

            player_instance = Player(name=name, club=club[0], position=position, link=link, nationality=nationality)
            players.append(player_instance)

        except (IndexError, ValueError) as e:
            print(f"Error extracting player data: {e}")

    return players
    
def get_full_player_details(player: Player):
    response = requests.get(player.profile_link, headers=HEADERS)
    if response.status_code == 200:
        content = response.text
        pattern = r'<div class="info-table[^>]*">(.*?)<\/div>'
        contents = re.findall(pattern, content, re.DOTALL)[0]
        span_pattern = r'<span[^>]*class="info-table__content[^>]*>(.*?)<\/span>'
        contents = re.findall(span_pattern, content, re.DOTALL)
        data_dict = {}
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
                        cleaned_value = cleaned_value.replace('m', 'cm').replace(',', '').strip()
                        data_dict["height"] = cleaned_value  
                    elif label in ["Full name:","Name in home country:"]:
                        data_dict["full_name"] = cleaned_value  
                    elif  label == "Foot:":
                        data_dict["foot"] = cleaned_value  
                    # if label and cleaned_value:
                    #      data_dict[label] = cleaned_value  
                    
        player.add_player_profile(data_dict["full_name"], data_dict["DOB"], data_dict["age"], data_dict["height"], data_dict["foot"])

def get_all_teams():
    url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1"
    response = requests.get(url, headers=HEADERS)
    html = response.text
    regex = r'<div id="yw1".*?>(.*?)</div>\s*?<div class="table-footer">'
    html = re.findall(regex, html, re.DOTALL)[0]
    regex = r'(even|odd)">(.*?)(<tr class="|</tbody>)'
    teams_html = re.findall(regex, html, re.DOTALL)
    regex = r'<td.*?>(.*?)</td>'
    title_regex = r'title="(.*?)"'
    link_regex = r'href="(.*?)"'
    for team_html in teams_html:
        team = re.findall(regex, team_html[1], re.DOTALL)
        name = re.findall(title_regex, team[0], re.DOTALL)[0].replace("&amp;", "&")
        link = "https://www.transfermarkt.com/" + re.findall(link_regex, team[0], re.DOTALL)[0]
        teams.append(Team(name, link))

def get_player_in_team(team: Team):
    response = requests.get(team.link, headers=HEADERS)
    html = response.text
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
        team.players.append(Player(number, name, link, nationalities))

def get_stats(player : Player):
    appearances = 0
    goals_or_clean_sheet = 0
    minutes_played = 0

    response = requests.get(player.stat_link, headers=HEADERS)
    if response.status_code == 200 :
        html = response.text
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
                appearances += int(re.findall(appearances_regex, td[2], re.DOTALL)[0])
                if player.position == 'goalkeeper':
                    goals_or_clean_sheet += int(td[6])
                    minute = td[7]
                    minutes_played += int(''.join(re.findall(r'\d+', minute)))
                else :
                    goals_or_clean_sheet += int(td[3])
                    minute = td[6]
                    minutes_played += int(''.join(re.findall(r'\d+', minute)))

        
get_all_teams()
for team in teams[:1]:
    get_player_in_team(team)
get_stats(teams[0].players[0])
# get_full_player_details(teams[0].players[0])
# print(teams[0].players[0].__dict__)
