import re

class Player:
    def __init__(self, name, club, position, nationality, link, status='Active'):
        self.name = name
        self.club = club
        self.position = position
        self.nationality = nationality
        self.status = status
        self.link = link

    def __repr__(self):
        return f"Player(name={self.name}, club={self.club}, position={self.position}, nationality={self.nationality}, status={self.status})"

    def to_dict(self):
        return {
            "name": self.name,
            "club": self.club,
            "position": self.position,
            "nationality": self.nationality,
            "status": self.status,
            "link": self.link
        }

def playerFromTransfer(html) -> list[Player]:
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

def getMaxPagination(html) -> int: 
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