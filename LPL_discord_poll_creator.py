import bs4
import requests
import time
import re

# TODO: Create a tournament class, match class, teams class for organization
# TODO: refactor a bunch
# TODO: See if there is an LPL api instead of scraping cancer
# TODO: Update tournament and matches by periodically querying LPL website with a async listener.
# TODO: Add discord integration (as a bot?): write poll creation commands, close polls when tournament/match finishes, tally results, create prediction leaderboard
# TODO: Database structure can be simple json of user: predictions and match: result. Compute leaderboard and user predictioin stats from there
# TODO: Make deployable bundle...venv, docker, heroku whatever


def tableDataText(table):
    """
    Parses a html segment started with tag <table> followed
    by multiple <tr> (table rows) and inner <td> (table data) tags.
    It returns a list of rows with inner columns.
    Accepts only one <th> (table header/data) in the first row.
    """

    def rowgetDataText(tr, coltag="td"):  # td (data) or th (header)
        return [td.get_text(strip=True) for td in tr.find_all(coltag)]

    rows = []
    trs = table.find_all("tr")
    headerow = rowgetDataText(trs[0], "th")
    if headerow:  # if there is a header row include first
        rows.append(headerow)
        trs = trs[1:]
    for tr in trs:  # for every table row
        rows.append(rowgetDataText(tr, "td"))  # data row
    return rows


def get_tournament_title(tournament_url):
    tournament_request = requests.get(tournament_url)

    if tournament_request.status_code == requests.codes.ok:
        tournament_html = bs4.BeautifulSoup(
            tournament_request.content, features="html5lib"
        )
        title = tournament_html.find("h1").get_text()

    return title


def get_teams_dict(teams_url):
    # Parse Teams into dictionary of teamname: 'player_list'
    teams = {}
    if not teams_url:
        return teams

    teams_request = requests.get(teams_url)

    if teams_request.status_code == requests.codes.ok:
        teams_html = bs4.BeautifulSoup(teams_request.content, features="html5lib")
        table = teams_html.find("table")
        rows = tableDataText(table)

        for row in rows[1:]:  # exclude first row headers [Teams, Players]
            teams[row[0]] = row[1]

    return teams


def get_matches_dict(matches_url):
    # Parses Matches into

    matches = []
    if not matches_url:
        return matches

    matches_request = requests.get(matches_url)

    if matches_request.status_code == requests.codes.ok:
        matches_html = bs4.BeautifulSoup(matches_request.content, features="html5lib")
        tables = matches_html.findAll("table")
        rows = []
        for table in tables:
            rows.append(tableDataText(table))

    # if 2 tables, double elim with first being losers and second being main
    # if 1 table, single elim or double elim where table is maini bracket
    if len(tables) > 1:
        for row in rows[0][1:]:
            match = {}
            match["bracket"] = "Losers"
            match["title"] = row[0]
            match["team1"] = row[0].split(" vs ")[0]
            match["team2"] = row[0].split(" vs ")[1]
            match["map"] = row[1]
            match["status"] = row[2]
            match["round"] = row[3]
            matches.append(match)

        for row in rows[1][1:]:
            match = {}
            match["bracket"] = "Main"
            match["title"] = row[0]
            match["team1"] = row[0].split(" vs ")[0]
            match["team2"] = row[0].split(" vs ")[1]
            match["map"] = row[1]
            match["status"] = row[2]
            match["round"] = row[3]
            matches.append(match)
    else:
        match = {}
        match["bracket"] = "Main"
        match["title"] = row[0]
        match["team1"] = row[0].split(" vs ")[0]
        match["team2"] = row[0].split(" vs ")[1]
        match["map"] = row[1]
        match["status"] = row[2]
        match["round"] = row[3]
        matches.append(match)

    return matches


def generate_winner_prediction_poll(teams, poll_title):
    """
    Returns a string to be used as a command for Simple Poll in the format of:
    /poll "Who will win today?" "Team1" "Team2" "Team3"
    """
    print("\nGENERATING TOURNAMENT WINNER PREDICTION POLL...")
    output = "/poll " + '"' + poll_title + '" '

    for team_name, team_players in teams.items():
        team_name = re.sub(r"(\S)\(", r"\1 (", team_name)
        poll_option = '"' + team_name + ": " + team_players + '" '
        output = output + poll_option

    print(output)
    return output


def generate_match_prediction_poll(match):
    """
    Returns a string to be used as a command for Simple Poll in the format of:
    /poll "Who will win Team1 vs Team2?" "Team1" "Team2"
    """
    # print("\nGENERATING MATCH POLL...")
    poll_title_description = " (" + match["bracket"] + " Round: " + match["round"] + ")"
    poll_title = match["title"] + poll_title_description
    output = (
        "/poll "
        + '"'
        + poll_title
        + '" '
        + '"'
        + match["team1"]
        + '" '
        + '"'
        + match["team2"]
        + '" '
    )

    print(output)
    return output


if __name__ == "__main__":

    BASE_URL = "https://eu.letsplay.live/tournaments/18109"
    if not BASE_URL:
        BASE_URL = input(
            "Enter the tournament page (e.g. https://eu.letsplay.live/tournaments/18109) \n\n"
        )

    MATCHES_URL = BASE_URL + "/matches/"
    TEAMS_URL = BASE_URL + "/teams/"

    # Parse
    teams = get_teams_dict(TEAMS_URL)
    matches = get_matches_dict(MATCHES_URL)

    # Generate Poll Creation Strings
    tournament_title = get_tournament_title(BASE_URL)
    winner_prediction_poll_title = f"Who will win {tournament_title}?"
    generate_winner_prediction_poll(
        teams=teams, poll_title=winner_prediction_poll_title
    )
    for match in matches:
        generate_match_prediction_poll(match)
