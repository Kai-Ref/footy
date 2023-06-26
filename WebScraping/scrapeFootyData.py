from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

def get_teams(url):
    # exception handling
        r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(r)
        bs = BeautifulSoup(html, 'html.parser')
        
        # Get the team names
        team_rows = bs.find('table', {'class': 'items'}).find_all('td', {"class":"hauptlink no-border-links"})
        
        teams = {}
        for row in team_rows:
            team_name = row.text.strip().split(' \\')[0]
            team_href = row.find('a')['href']
            team_id = team_href.split('/')[4]
            teams[team_name]={'href': team_href, 'id': team_id}
        return teams

def get_players(team_url):
    r = Request(team_url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(r)
    bs = BeautifulSoup(html, 'html.parser')
    # Get the team names
    player_rows = bs.find('table', {'class': 'items'}).find_all('span', {"class":"hide-for-small"})
    players = {}
    for row in player_rows:
        if "wechsel-kader-wappen" in row["class"]:# skip entries not linked to players
            continue
        player_name = row.text
        player_href = row.find("a")["href"]
        player_id = player_href.split("/")[-1]
        players[player_name] = {"player_href": player_href, "player_id":player_id}
    
    player_dates, player_numbers = [], []
    team_rows = bs.find('table', {'class': 'items'}).find_all('td', {"class":"zentriert"})
    for row in team_rows:
        if row.get_text()== '':
            continue
        elif len(row.get_text())>=3:
            player_dates.append(row.get_text())
        else:
            player_numbers.append(row.get_text())

    # not ideal but add the dates and numbers based on their index position
    if len(players.keys()) == len(player_dates) & len(players.keys()) == len(player_numbers):
        for player_name in players.keys():
            players[player_name]["Birthday"] = player_dates[list(players.keys()).index(player_name)]
            players[player_name]["Number"] = player_numbers[list(players.keys()).index(player_name)]
    else:
        print("Not matching dates and/or numbers")
    # Create a DataFrame from the dictionary
    player_df = pd.DataFrame.from_dict(players, orient='index').reset_index(drop=False, names="players")
    return player_df

def get_player_info(url, team_id):
    # retrieves information from a players web site
    r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(r)
    bs = BeautifulSoup(html, 'html.parser')
    
    player_info = {}
    player_info["player_id"] = url.split("/")[-1]
    # age
    '''
    try:  
        age = bs.find_all("div", {"class":"info-table info-table--right-space"})[0].find("span", {"class": "info-table__content info-table__content--bold"}).find("a").get_text()
    except TypeError:
            age = 
    print(age)
    '''
    # Get the team names
    hrefs, transfer_years, club_ids = [], [], []
    grid = bs.find_all("div", {"class":"tm-player-transfer-history-grid"})
    for entry in grid:
        old_club = entry.find("div", {"class":"tm-player-transfer-history-grid__old-club"})
        if None == old_club: # handle None matches
            continue
        else:
            if "grid__heading" in old_club["class"]:# exclude the header
                continue
            try:
                href = old_club.find("a", {"class":"tm-player-transfer-history-grid__club-link"})["href"]
            except TypeError as e:
                href = old_club.find("a")["href"]
            transfer_year = href.split("/")[-1]
            club_id = href.split("/")[-3]
            hrefs.append(href)
            transfer_years.append(transfer_year)
            club_ids.append(club_id)
    player_info["transfer_hrefs"] = hrefs
    player_info["transfer_years"] = transfer_years
    club_ids.insert(0, team_id)
    player_info["transfer_club_ids"] = club_ids

    # market value
    current_mv = bs.find_all("div", {"class":"tm-player-market-value-development__current-value"})
    for entry in current_mv:
        player_current_mv = entry.get_text()
    player_info["current_mv"] = player_current_mv

    # max market value
    max_mv = bs.find_all("div", {"class":"tm-player-market-value-development__max-value"})
    for entry in max_mv:
        player_max_mv = entry.get_text()
    player_info["max_mv"]= player_max_mv
    
    # position
    player_positions = []
    positions = bs.find_all("dd", {"class":"detail-position__position"})
    for position in positions:
        player_positions.append(position.get_text())
    player_main_position = [player_positions[0]]
    player_info["main_position"] = player_main_position
    if len(player_positions)>1: 
        player_other_positions = player_positions[1:]
        player_info["other_positions"] = player_other_positions

    # nationality
    player = bs.find('div', {'class': 'info-table'})
    nations = player.find_all("img", {"class": "flaggenrahmen"})
    player_nations = []
    for nation in nations:
        if "lazy" in nation["class"]:
            continue
        player_nations.append(nation["title"])
    player_info["nationality"] = player_nations
    player_info = {key: [value] for key, value in player_info.items()}
    player_info_df = pd.DataFrame(player_info)
    return player_info_df

def load_players_info_for_team(team_url, base_url, team_name):
    # combine the information derived from get_players and get_player_info
    team_id = team_url.split('/')[-1]
    print(team_id)
    df = get_players(team_url)
    additional_df = pd.DataFrame()
    for href in df.player_href:
        href = base_url + href
        player_info_df = get_player_info(href, team_id)
        additional_df = pd.concat([additional_df, player_info_df], axis=0)
    df = pd.merge(df, additional_df, on="player_id", how="left")
    df.to_csv(f'{team_name}.csv')


if __name__ == "__main__":
    #url = "https://www.transfermarkt.de/bundesliga/startseite/wettbewerb/L1.html"
    base_url = "https://www.transfermarkt.com"
    bremen = base_url + "/hertha-bsc/startseite/verein/44"
    load_players_info_for_team(bremen, base_url, team_name="Hertha BSC")

    '''    r = Request(bremen, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(r)
    bs = BeautifulSoup(html, 'html.parser')
    # Get the team names
    team_rows = bs.find('table', {'class': 'items'}).find_all('td', {"class":"zentriert"})
    for row in team_rows:
        if row.get_text()== '':
            continue
        elif len(row.get_text())>=3:
            player_date = row.get_text()
            print(player_date)
        else:
            player_number = row.get_text()
            print( player_number)'''
        

    #urls = ["/bundesliga/startseite/wettbewerb/L1", "/premier-league/startseite/wettbewerb/GB1",
      #      "/primera-division/startseite/wettbewerb/ES1", "/serie-a/startseite/wettbewerb/IT1",
       #     "/ligue-1/startseite/wettbewerb/FR1"]
    #ducksch = base_url + "/marvin-ducksch/profil/spieler/125103"
    #senninger = base_url + "/fabian-senninger/profil/spieler/334490"

    #for url in [senninger, ducksch]:
     #   r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
      #  html = urlopen(r)
       # bs = BeautifulSoup(html, 'html.parser')
    
    # urls = [ base_url + url for url in urls]
    # for url in urls:
        # teams = get_teams(url)
        # print(teams)