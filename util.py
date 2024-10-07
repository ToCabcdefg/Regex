from   datetime import datetime
import re
import time
import requests
from cache_config import cache
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
        self.transfer_link = self.profile_link.replace("profil", "transfers")
        self.award_link = self.profile_link.replace("profil", "erfolge")
        self.nationalities = nationalities
        self.awards = []
        self.club_history = []
        
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
            "DOB": self.DOB +" (" + self.age + ")",
            "age": self.age,
            "height": self.height[:-2],
            "foot": self.foot,
            "awards": self.awards,
            "appearances": self.appearances,
            "goals": self.goals,
            "minutes_played": self.minutes_played,
            "club_history": self.club_history
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

teams = []

def get_cached_response(url):
    return cache.get(url)

def get_transfer_content(url, max_retries=3, wait_time=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    
    driver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)

        for attempt in range(max_retries):
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "iframe"))
                )
                break
            except Exception:
                print(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        if not driver.find_elements(By.TAG_NAME, "iframe"):
            print("No iframes found after retries.")
            return None

        driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[1])

        accept_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//button[@title='Accept & continue']"))
        )
        accept_button.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tm-transfer-history'))
        )
        transfer_history_element = driver.find_element(By.CLASS_NAME, 'tm-transfer-history')
        driver.execute_script("arguments[0].scrollIntoView();", transfer_history_element)

        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'tm-player-transfer-history-grid'))
        )

        return driver.page_source

    finally:
        driver.quit()
        
def custom_request(url, selenium=False):
    response = get_cached_response(url)
    if response is not None:
        return response

    if selenium:
        content = get_transfer_content(url)
        cache.set(url, content, timeout=36000)
        return content
    else:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            cache.set(url, response.text, timeout=36000)
            return response.text
    
def get_player_details(player: Player):
    content = custom_request(player.profile_link)
    pattern = r'<div class="info-table[^>]*">(.*?)<\/div>'
    contents = re.findall(pattern, content, re.DOTALL)[0]
    span_pattern = r'<span[^>]*class="info-table__content[^>]*>(.*?)<\/span>'
    contents = re.findall(span_pattern, content, re.DOTALL)
    data_dict = {"full_name": player.name, "DOB": "14/09/1995", "age": "29", "height": "180cm", "foot": "right"}
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
            appearances += int(re.findall(appearances_regex, td[2], re.DOTALL)[0])
            if player.position == 'goalkeeper':
                goals_or_clean_sheet += int(td[6])
                minute = td[7]
                minutes_played += int(''.join(re.findall(r'\d+', minute)))
            else :
                goals_or_clean_sheet += int(td[3])
                minute = td[6]
                minutes_played += int(''.join(re.findall(r'\d+', minute)))
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
        name = re.findall(title_regex, team[0], re.DOTALL)[0].replace("&amp;", "&")
        link = "https://www.transfermarkt.com/" + re.findall(link_regex, team[0], re.DOTALL)[0]
        teams.append(Team(name, link))

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
        team.players.append(Player(number, name, link, nationalities))

def init_data():
    get_all_teams()
    for team in teams:
        team.players = []
        get_player_in_team(team)
        for player in team.players: 
            get_player_details(player)
            get_player_awards(player)
            get_player_club(player)
            print(player.name)

def get_all_players():
    res = []
    for team in teams: 
        for player in team.players:
            res.append(player.to_dict())
    print(len(res))
    return res
