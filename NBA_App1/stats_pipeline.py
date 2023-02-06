import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np

import matplotlib
from flask import url_for

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import base64
import os
import io
from io import BytesIO

import time
import datetime

import urllib

team_names =     ['Utah Jazz', 'Sacramento Kings', 'Washington Wizards',
                  'Boston Celtics', 'Milwaukee Bucks', 'Oklahoma City Thunder',
                  'Chicago Bulls', 'Phoenix Suns', 'Philadelphia 76ers',
                  'New Orleans Pelicans', 'Charlotte Hornets', 'Los Angeles Lakers',
                  'Indiana Pacers', 'Toronto Raptors', 'Cleveland Cavaliers',
                  'Denver Nuggets', 'Minnesota Timberwolves', 'Brooklyn Nets',
                  'San Antonio Spurs', 'Dallas Mavericks', 'Houston Rockets',
                  'Detroit Pistons', 'Portland Trail Blazers', 'Atlanta Hawks',
                  'Golden State Warriors', 'Miami Heat', 'Los Angeles Clippers',
                  'New York Knicks', 'Memphis Grizzlies', 'Orlando Magic', 'League Average']

team_names_nocity = ['Jazz', 'Kings', 'Wizards', 'Celtics', 'Bucks', 'Thunder',
                     'Bulls', 'Suns', '76ers', 'Pelicans', 'Hornets', 'Lakers',
                     'Pacers', 'Raptors', 'Cavaliers', 'Nuggets', 'Timberwolves', 'Nets',
                     'Spurs', 'Mavericks', 'Rockets', 'Pistons', 'Trail Blazers', 'Hawks',
                     'Warriors', 'Heat', 'Clippers', 'Knicks', 'Grizzlies', 'Magic', 'League Average']

team_abbrs =     ['UTA', 'SAC', 'WAS', 'BOS', 'MIL', 'OKC', 'CHI', 'PHX', 'PHI',
                  'NOP', 'CHA', 'LAL', 'IND', 'TOR', 'CLE', 'DEN', 'MIN', 'BKN',
                  'SAS', 'DAL', 'HOU', 'DET', 'POR', 'ATL', 'GSW', 'MIA', 'LAC',
                  'NYK', 'MEM', 'ORL', 'NBA']

team_name_abbr_dict = {}
team_abbr_name_dict = {}
team_nocity_name_dict = {}

for i in range(len(team_names)):
    team_name_abbr_dict[team_names[i]]=team_abbrs[i]

for i in range(len(team_abbrs)):
    team_abbr_name_dict[team_abbrs[i]]=team_names[i]

for i in range(len(team_names)):
    team_nocity_name_dict[team_names_nocity[i]]=team_names[i]


def scrape_player_boxscores():
    url = 'https://stats.nba.com/stats/leaguegamelog'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/96.0.4664.110 Safari/537.36',
        'Referer': 'https://www.nba.com/'}
    payload = {
        'Counter': '1000',
        'DateFrom': '',
        'DateTo': '',
        'Direction': 'DESC',
        'LeagueID': '00',
        'PlayerOrTeam': 'P',
        'Season': '2022-23',
        'SeasonType': 'Regular Season',
        'Sorter': 'DATE'}

    jsonData = requests.get(url, headers=headers, params=payload).json()

    rows = jsonData['resultSets'][0]['rowSet']
    columns = jsonData['resultSets'][0]['headers']

    df_players = pd.DataFrame(rows, columns=columns)
    df_players['DATE_MATCHUP'] = df_players['GAME_DATE'].str[5:] + ' ' + df_players['MATCHUP'].str[4:]
    df_players = df_players.fillna(0)
    return df_players


def scrape_team_boxscores():
    url = 'https://stats.nba.com/stats/leaguegamelog'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Referer': 'https://www.nba.com/'}
    payload = {
        'Counter': '1000',
        'DateFrom': '',
        'DateTo': '',
        'Direction': 'DESC',
        'LeagueID': '00',
        'PlayerOrTeam': 'T',
        'Season': '2022-23',
        'SeasonType': 'Regular Season',
        'Sorter': 'DATE'}

    jsonData = requests.get(url, headers=headers, params=payload).json()

    rows = jsonData['resultSets'][0]['rowSet']
    columns = jsonData['resultSets'][0]['headers']

    df = pd.DataFrame(rows, columns=columns)
    df.drop(['VIDEO_AVAILABLE'], axis=1, inplace=True)

    df['FG2M'] = df.FGM - df.FG3M
    df['FG2A'] = df.FGA - df.FG3A

    df['FG2_PTS'] = df.FG2M * 2
    df['FG3_PTS'] = df.FG3M * 3

    df['FRAC_ATT_2PT'] = df.FG2A / df.FGA
    df['FRAC_ATT_3PT'] = df.FG3A / df.FGA

    df['FRAC_MK_2PT'] = df.FG2M / df.FGM
    df['FRAC_MK_3PT'] = df.FG3M / df.FGM

    df['FRAC_PTS_2PT'] = df.FG2_PTS / df.PTS
    df['FRAC_PTS_3PT'] = df.FG3_PTS / df.PTS
    df['FRAC_PTS_FT'] = df.FTM / df.PTS

    df['OPP_TEAM_ABBR'] = df['MATCHUP'].str.strip().str[-3:]
    df['OPP_PTS'] = df['PTS'] - df['PLUS_MINUS']

    df['MONTH'] = pd.DatetimeIndex(df['GAME_DATE']).month
    df['YEAR'] = pd.DatetimeIndex(df['GAME_DATE']).year

    def home_or_away(string):
        if string[4] == '@':
            return 'AWAY'
        elif string[4] == 'v':
            return 'HOME'

    df['HOME_AWAY'] = df['MATCHUP'].map(home_or_away)

    conferences = {'GSW': 'WEST', 'POR': 'WEST', 'SAC': 'WEST', 'UTA': 'WEST', 'MIA': 'EAST', 'DEN': 'WEST',
                   'MIN': 'WEST',
                   'PHI': 'EAST', 'NOP': 'EAST', 'ORL': 'EAST', 'MIL': 'EAST', 'CHI': 'EAST', 'DET': 'EAST',
                   'TOR': 'EAST',
                   'PHX': 'WEST', 'LAL': 'WEST', 'ATL': 'EAST', 'WAS': 'EAST', 'MEM': 'WEST', 'CLE': 'EAST',
                   'LAC': 'WEST',
                   'BOS': 'EAST', 'NYK': 'EAST', 'IND': 'EAST', 'CHA': 'EAST', 'SAS': 'WEST', 'HOU': 'WEST',
                   'DAL': 'WEST',
                   'OKC': 'WEST', 'BKN': 'EAST'}

    df['CONFERENCE'] = df['TEAM_ABBREVIATION'].apply(lambda x: conferences.get(x))
    df['OPP_CONFERENCE'] = df['OPP_TEAM_ABBR'].apply(lambda x: conferences.get(x))

    # ADD OPONENTS RECORD ON GAME DATE
    # ADD TEAM RECORD ON GAME DATE

    df['DATE_MATCHUP'] = df['GAME_DATE'].str[5:] + ' ' + df['MATCHUP'].str[4:]
    # df['DATE_MATCHUP'] = df['GAME_DATE'] + ' ' + df['MATCHUP'].str[4:]

    df.TEAM_NAME = df.TEAM_ABBREVIATION.apply(lambda x: team_abbr_name_dict.get(x))

    html = df.to_html()

    return df


def scrape_player_hwa(df, name):
    player_id = int(df[df.PLAYER_NAME == name].PLAYER_ID.unique())
    formatted_name = str(name).replace(' ', '-').lower()
    opts = Options()
    opts.add_argument("--headless")

    url = f"https://www.nba.com/player/{player_id}/{formatted_name}/profile"

    chrome_driver = "C:\\Users\\Peter\\Downloads\\chromedriver_win32\\chromedriver.exe"
    driver = webdriver.Chrome(options=opts, service=Service(chrome_driver))
    driver.set_page_load_timeout(20)
    time.sleep(1)
    driver.set_window_size(2000, 900)
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    out1 = soup.find("div", class_="PlayerSummary_statsDetails__FRW2E")

    out2 = out1.find_all('p', class_="PlayerSummary_playerStatLabel__I3TO3")[0].text

    return out2


def career_summary(df, name):
    def process_bio(text):
        result = str(text)
        try:
            result = result.replace("PROFESSIONAL CAREER", "<br><br><b>PROFESSIONAL CAREER</b><br>")
            try:
                result = result.replace("BEFORE NBA", "<br><br><b>BEFORE NBA</b><br>")
            except:
                pass
            try:
                result = result.replace("PERSONAL LIFE", "<br><br><b>PERSONAL LIFE</b><br>")
            except:
                pass
            return result
        except:
            return text

    try:
        player_id = int(df[df.PLAYER_NAME == name].PLAYER_ID.unique())
        formatted_name = str(name).replace(' ', '-').lower()
        html = requests.get(f'https://www.nba.com/player/{str(player_id)}/{formatted_name}/bio').content
        soup = BeautifulSoup(html, 'html.parser')
        divs = str(soup.find_all("div", class_="PlayerBio_player_bio__kIsc_")[0].text).replace('\r\n', ' ')
        output = process_bio(divs)
        return output

    except:
        pass


def player_stat_plot(df, name, stat):
    plt.rcParams["figure.figsize"] = (20, 12)
    fig, ax = plt.subplots(nrows=1, ncols=1)
    fig.set_facecolor('#BDF3FF')

    df = df[df.PLAYER_NAME == name].sort_values(by='GAME_DATE').reset_index(drop=True)

    plt.plot(df.index, df[stat], marker='o', color='royalblue', label='Single Game')

    if df.GAME_DATE.count() > 5:
        rolling_mean_5 = df[stat].rolling(5).mean()
        plt.plot(rolling_mean_5, color="Purple", linestyle='dashed', alpha=1, marker='o', label="5 Game Mean")

    if df.GAME_DATE.count() > 1:
        z = np.polyfit(df.index, df[stat], 1)
        p = np.poly1d(z)
        plt.plot(df.index, p(df.index), linestyle='dotted', linewidth=3, color='darkorange', label='Season Trend')

    plt.legend(loc='best', fontsize=17)

    plt.xticks(df.index, df["DATE_MATCHUP"].values)
    plt.xticks(rotation=75, size=13, fontweight='bold')

    if df[stat].max() > 30:
        plt.yticks(list(range(0, df[stat].max() + 10, 10)), size=16, fontweight='bold')
    elif df[stat].max() <= 30:
        plt.yticks(list(range(0, df[stat].max(), 5)), size=16, fontweight='bold')
    elif df[stat].max() <= 5:
        plt.yticks(list(range(0, df[stat].max() + 1, 1)), size=16, fontweight='bold')

    plt.ylim(0, None)
    plt.yticks(fontsize=20)
    plt.title(f'{name} {stat} by Game', fontsize=32, fontweight='bold')

    plt.xlabel('MATCHUP', fontsize=25, fontweight='bold')
    plt.ylabel(stat, fontsize=25, fontweight='bold')

    if not os.path.exists(f'static/NBA_player_{stat}_plots'):
        os.mkdir(f'static/NBA_player_{stat}_plots')

    plot_file = f'static/NBA_player_{stat}_plots/{name}_{stat}.png'
    plt.savefig(plot_file, bbox_inches='tight')

    return plot_file


def plus_minus_plot(df, team_name):

    sns.set(rc={'figure.figsize': (18, 12)})

    df = df[df.TEAM_NAME==team_name].sort_values(by='GAME_DATE').reset_index(drop=True)

    values = np.array(df.PLUS_MINUS)
    pal = ['green' if (i > 0) else 'red' for i in values]

    ax1 = sns.barplot(data=df, x=df.index, y=values, palette=pal)

    ax1.bar_label(ax1.containers[0], fontsize=16, fontweight='bold')
    plt.title(f"Plus/Minus by Game for {team_name}", fontsize=20, fontweight='bold')

    ax2 = sns.lineplot(data=df, x=df.index, y="PLUS_MINUS", linestyle='--', color='blue', marker='o')
    plt.xticks(rotation=85)
    plt.axhline(y=0, color='r', linestyle='--')

    plt.xticks(df.index, df["DATE_MATCHUP"].values, fontsize=13, fontweight='bold')
    plt.xlabel('MATCHUP', fontsize=20, fontweight='bold')

    plt.yticks(rotation=0, fontsize=20, fontweight='bold')
    plt.ylabel('PLUS/MINUS', fontsize=20, fontweight='bold')

    if not os.path.exists('static/NBA_plus_minus_plots'):
        os.mkdir('static/NBA_plus_minus_plots')

    plot_file = f'static/NBA_plus_minus_plots/{team_name}.png'

    plt.savefig(plot_file, bbox_inches='tight')

    return plot_file


def line_plot_scores(df, team_name):

    plt.clf()

    plt.rcParams["figure.figsize"] = (22, 12)
    fig, ax = plt.subplots(nrows=1, ncols=1)
    fig.set_facecolor('#BDF3FF')

    team_abbr = str(df[df.TEAM_NAME==team_name].TEAM_ABBREVIATION.unique()[0])

    df = df[df.TEAM_NAME==team_name].sort_values(by='GAME_DATE').reset_index(drop=True)

    plt.plot(df.index, df['PTS'], marker='.', linewidth=1.5, label=team_abbr, color='blue')

    z = np.polyfit(df.index, df['PTS'], 1)
    p = np.poly1d(z)
    plt.plot(df.index, p(df.index), linestyle='dotted', linewidth=1.5, color='dodgerblue',
                          label=f'{team_abbr} SEASON TREND')

    plt.plot(df.index, df['OPP_PTS'], marker='.', label='OPP', linewidth=1.5, color='red')
    z = np.polyfit(df.index, df['OPP_PTS'], 1)
    p = np.poly1d(z)
    plt.plot(df.index, p(df.index), linestyle='dotted', linewidth=1.5, color='salmon',
                         label='OPP SEASON TREND')

    plt.legend(loc='best', fontsize=10)
    plt.title(f'{team_abbr} vs OPP Scores', fontsize=18, fontweight='bold')
    plt.xticks(df.index, df["DATE_MATCHUP"].values, rotation=85, fontsize=12)
    plt.yticks(list(range(0, 160, 10)), fontsize=14)
    plt.ylim(70, 150)
    plt.xlabel('MATCHUP', fontsize=16, fontweight='bold')
    plt.ylabel('PTS', fontsize=16, fontweight='bold')

    if not os.path.exists('static/NBA_scores_plots'):
        os.mkdir('static/NBA_scores_plots')

    plot_file = f'static/NBA_scores_plots/{team_name}.png'

    plt.savefig(plot_file, bbox_inches='tight')

    return plot_file


def scrape_daily_injuries():
    opts = Options()
    opts.add_argument("--headless")

    url = "https://www.cbssports.com/nba/injuries/"

    chrome_driver = "chromedriver_win32\\chromedriver.exe"
    driver = webdriver.Chrome(options=opts, service=Service(chrome_driver))
    driver.set_page_load_timeout(20)
    time.sleep(1)
    driver.set_window_size(2100, 9000)
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    team_injuries = soup.find_all('div', class_="TableBaseWrapper")
    team_data = []
    for team in team_injuries:
        team_name = team.find("div", class_="TeamLogoNameLockup-name").text
        players = team.find_all('tr', class_="TableBase-bodyTr")
        for player in players:
            player_data = {}
            player_data['Team'] = team_name
            player_data['Name'] = player.find('span', class_="CellPlayerName--long").text
            player_data['POS'] = player.find_all('td', class_="TableBase-bodyTd")[1].text.lstrip('\n ')
            player_data['Updated'] = player.find('span', class_="CellGameDate").text.lstrip('\n \n ').rstrip('\n ')
            player_data['Injury'] = player.find_all('td', class_="TableBase-bodyTd")[3].text.lstrip('\n ')
            player_data['Status'] = player.find_all('td', class_="TableBase-bodyTd")[4].text.lstrip('\n ')
            team_data.append(player_data)
    driver.quit()

    df = pd.DataFrame(team_data).sort_values('Team')

    for i in df.Team.unique():
        df_team = df[df.Team == str(i)]

    return df.to_html(index=False, classes='inj')


def today_matchups():
    opts = Options()
    opts.add_argument("--headless")

    url = f"https://www.espn.com/nba/scoreboard/_/date/{datetime.datetime.today().strftime('%Y%m%d')}"

    chrome_driver = "chromedriver_win32\\chromedriver.exe"

    driver = webdriver.Chrome(options=opts, service=Service(chrome_driver))

    driver.set_page_load_timeout(5)
    time.sleep(1)
    driver.set_window_size(2100, 9000)

    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    date = datetime.datetime.today().strftime("%m-%d-%y")

    games = soup.find_all("div", class_='Scoreboard__Row flex w-100 Scoreboard__Row__Main')
    games_data = []
    try:
        for game in games:
            game_data = {}
            away_tm = \
                game.find_all("div", class_="ScoreCell__TeamName ScoreCell__TeamName--shortDisplayName truncate db")[0]
            home_tm = \
                game.find_all("div", class_="ScoreCell__TeamName ScoreCell__TeamName--shortDisplayName truncate db")[1]
            game_data['Date'] = date
            try:
                game_data['Time'] = game.find("div",
                                              class_="ScoreCell__Time ScoreboardScoreCell__Time h9 clr-gray-03").text
            except:
                try:
                    game_data['Time'] = game.find("div",
                                                  class_="ScoreCell__Time ScoreboardScoreCell__Time h9 clr-gray-01").text
                except:
                    try:
                        game_data['Time'] = game.find("div",
                                                      class_="ScoreCell__Time ScoreboardScoreCell__Time h9 clr-negative").text
                    except:
                        pass

            game_data["Away"] = away_tm.text
            # game_data["away_tm_abbr"] = team_names_nocity_dict[away_tm.text]

            try:
                game_data["Away Score"] = game.find_all("div",
                                                        class_="ScoreCell__Score h4 clr-gray-01 fw-heavy tar ScoreCell_Score--scoreboard pl2")[0].text
            except:
                game_data['Away Score'] = 0

            game_data["Home"] = home_tm.text
            # game_data["home_tm_abbr"] = team_names_nocity_dict[home_tm.text]

            try:
                game_data["Home Score"] = game.find_all("div",
                                                        class_="ScoreCell__Score h4 clr-gray-01 fw-heavy tar ScoreCell_Score--scoreboard pl2")[1].text
            except:
                game_data['Home Score'] = 0

            games_data.append(game_data)
    except:
        pass
    df = pd.DataFrame(games_data)
    driver.quit()

    html_table = df.to_html(index=False, escape=False)

    return html_table

today_matchups()

def scrape_player_image(df, name):
    player_id = int(df[df.PLAYER_NAME == name].PLAYER_ID.unique())
    pic_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"

    response = requests.get(pic_url)
    image_data = response.content
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    image_data_uri = f'data:image/png;base64,{image_base64}'

    return image_data_uri
