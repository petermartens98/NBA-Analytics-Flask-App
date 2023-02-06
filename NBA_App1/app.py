from flask import Flask, render_template, url_for, request, redirect, send_file

from bs4 import BeautifulSoup

from stats_pipeline import scrape_player_boxscores, \
    scrape_team_boxscores, \
    career_summary, \
    player_stat_plot, \
    plus_minus_plot, \
    scrape_daily_injuries, \
    today_matchups, \
    scrape_player_image, \
    scrape_player_hwa, \
    line_plot_scores

team_names = ['Utah Jazz', 'Sacramento Kings', 'Washington Wizards',
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

team_abbrs = ['UTA', 'SAC', 'WAS', 'BOS', 'MIL', 'OKC', 'CHI', 'PHX', 'PHI',
              'NOP', 'CHA', 'LAL', 'IND', 'TOR', 'CLE', 'DEN', 'MIN', 'BKN',
              'SAS', 'DAL', 'HOU', 'DET', 'POR', 'ATL', 'GSW', 'MIA', 'LAC',
              'NYK', 'MEM', 'ORL', 'NBA']

team_name_abbr_dict = {}
team_abbr_name_dict = {}
team_nocity_name_dict = {}

for i in range(len(team_names)):
    team_nocity_name_dict[team_names_nocity[i]]=team_names[i]

for i in range(len(team_names)):
    team_name_abbr_dict[team_names[i]] = team_abbrs[i]

for i in range(len(team_abbrs)):
    team_abbr_name_dict[team_abbrs[i]] = team_names[i]

df_players_boxscores = scrape_player_boxscores()
df_player_averages = ''

df_teams_boxscores = scrape_team_boxscores()

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/player_reports_page", methods=['GET', 'POST'])
def player_page():
    if request.method == "GET":
        players = sorted(list(df_players_boxscores.PLAYER_NAME.unique()))
        player_name = str(request.args.get("player_name", 'Donovan Mitchell'))
        player_name_formatted = str(player_name.replace(' ', '_').replace("'", ""))
        try:
            player_team = str(
                df_players_boxscores[df_players_boxscores.PLAYER_NAME == player_name].TEAM_NAME.unique().item())
            team_name_formatted = player_team.replace(" ", "-").lower()
        except:
            player_team = ""

        try:
            career_summary(df_players_boxscores, player_name)
            player_summary = career_summary(df_players_boxscores, player_name)
        except:
            player_summary = ''

        try:
            pts_plot = player_stat_plot(df_players_boxscores, player_name, 'PTS')
        except:
            pts_plot = ''

        try:
            player_hwa = scrape_player_hwa(df_players_boxscores, player_name)
        except:
            player_hwa = ""

    player_img_file = scrape_player_image(df_players_boxscores, player_name)

    return render_template("player_reports_page.html",
                           players=players,
                           player_hwa=player_hwa,
                           player_name=player_name,
                           player_team=player_team,
                           team_image=f'static/NBA_Logos/{team_name_formatted}.png',
                           player_image=player_img_file,
                           player_summary=player_summary,
                           player_pts_plot_url=pts_plot)


@app.route("/team_reports_page", methods=['GET', 'POST'])
def team_page():
    if request.method == "GET":
        team_name = str(request.args.get("team_name", "Cleveland Cavaliers"))
        team_name_formatted = team_name.replace(" ", "-").lower()
        try:
            team_abbr = team_name_abbr_dict[team_name]
        except:
            team_abbr = ""
        teams = sorted(list(df_players_boxscores.TEAM_NAME.unique()))
        team_logo = f'static/NBA_Logos/{team_name_formatted}.png'
        try:
            line_plot_scores(df_teams_boxscores, team_name)
            points_plot = line_plot_scores(df_teams_boxscores, team_name)
        except:
            points_plot = ''

    return render_template('team_reports_page.html',
                           team_name=team_name,
                           team_logo=team_logo,
                           points_plot=points_plot,
                           teams=teams)


@app.route("/injuries_page", methods=['GET', 'POST'])
def injuries_page():
    today_injuries = scrape_daily_injuries()
    return render_template('injuries_page.html', today_injuries=today_injuries)


@app.route("/daily_matchups_page", methods=['GET', 'POST'])
def daily_mathchups_page():
    return render_template('daily_matchups_page.html', today_matchups=today_matchups())


if __name__ == "__main__":
    app.run(debug=False, port=3000)
