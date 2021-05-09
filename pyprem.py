from bs4 import BeautifulSoup 
import os, json
import urllib.request
import data

#
# Currently only supports premier league games. Other leagues will be added soon
#

class Search(object):
    '''
    This uses dicts in data.py to search for Premier League Fixtures.
    league should ALWAYS = epl, until more are added
    team = 'liverpool' or 'manchestercity', all lower case
    is results=True will show past games
    if fixtures=True will show future games
    '''
    def __init__(self, league, team, results, fixture):
        super(Search, self).__init__()

        # init the variables supplied
        self.league = league
        self.team = team
        self.results = results
        self.fixture = fixture
        self.data = data.variables
        
        # if a team is provided, search for their results
        if self.team:
            self.get_team_results_fixture()
        # if results or fixtures is set, do that
        else:
            if self.results or self.fixture:
                #this func covers both returning results and fixtures
                self.get_league_results_fixture()
            
            else:
                #currently broken as the table format is different
                self.get_league_table()
    
    # bc we're going to be doing this A LOT
    def get_html(self, url):
        '''
        Uses urllib.request to open a url and decode the HTML
        into utf8
        '''
        req = urllib.request.urlopen(url)
        content = req.read()

        html = content.decode('utf8')
        req.close()

        return html
    
    # aux so this doesnt all have to be in one function
    # will return either team results or fixtures based on
    # is_results.
    def get_team_results_fixture_aux(self, soup, is_results):

        if is_results:
            index = 0
        else: 
            index = 1
        # find all results in the soup, index 0 == past
        results = soup.find_all("div", {'class':'compgrp'})[index]
        # find all games in the result block
        games = results.find_all("table", {'class':'blocks'})

        # if we want results reverse them so they go from least->most recent
        if is_results:
            games = games[::-1]
        
        # loop over each game in the results
        for game in games:
            kick_off = game.find('td', {'class':'kick_t'}).text         # get the kick off time
            home_team = game.find('td', {'class':'home_o'}).text        # get the home team
            away_team = game.find('td', {'class':'away_o'}).text        # get the away team

            if is_results:
                score = game.find('td', {'class':'score'}).text         # if we want the score get it
                print(score)
            else:
                score = game.find('td', {'class': 'score'})             

                if score and not score.text == 'CANC':                  # check if the game is cancelled
                    score = '-'
                else:
                    score = 'CANC'
            # need to sort out a return value here
            if score != 'CANC':
                print (kick_off, home_team, score, away_team)
            
    def get_team_results_fixture(self):
        '''
        Get the results and/or fixtures for the given team.
        If we want results, it runs the aux func returning past fixtures
        If not, it gets future fixtures
        '''
        team = self.team
        league = self.league

        url = self.data[league][team]
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        if self.results:
            self.get_team_results_fixture_aux(soup, True)
        else:
            self.get_team_results_fixture_aux(soup, False)
    
    # another helper func for searching for an entire leagues results
    # prints off the previous rounds based on limit
    def get_league_results_fixture_aux(self, soup, limit=2):
        results = soup.find('div', {'id':'national'})
        rounds = results.find_all(True, {'class':['ncet', 'blocks']})

        num_rounds = 0
        for line in rounds:
            round_ = line.find('li', {'class':'ncet_round'})
            if round_:
                num_rounds += 1
                if num_rounds > limit:
                    break
                print(round_.text)
            else:
                game = line.find('tbody')
                kick_off_date = game.find('span', {'class':'kick_t_dt'}).text
                kick_off_time = game.find('span', {'class':'kick_t_ko'}).text
                home_team = game.find('td', {'class':'home'}).text
                away_team = game.find('td', {'class':'away'}).text
                score = game.find('td', {'class':'score'}).text
                
                print(kick_off_date, kick_off_time, home_team, score, away_team)
    

    def get_league_results_fixture(self):
        '''
        Calls the correct helper function for the input
        '''
        league = self.league

        if self.results:
            url = self.data[league]['_l_name_r']
            html = self.get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            self.get_league_results_fixture_aux(soup)
        
        if self.fixture:
            url = self.data[league]['_l_name_f']
            html = self.get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            self.get_league_results_fixture_aux(soup)
    
    def get_league_table(self):
        '''
        league = self.league
        url = self.data[league]['_l_name_t']
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find_all(True, {'id':'standings_1a'})
        print(table)
        # need to find the right class, its v weird
        teams = table.find_all('tr', {'class':['livetable__tableRow']})
        print("_ T P M W D L GF GA F")
        for team in teams:
            pos = team.find("td", {'class':'rank'}).text
            team_ = team.find("td", {'class':'team'}).text
            point = team.find("td", {'class':'point'}).text
            mp = team.find("td", {'class':'mp'}).text
            wins = team.find("td", {'class':'winx'}).text
            drawn = team.find("td", {'class':'draw'}).text
            lost = team.find("td", {'class':'lost'}).text
            goals = team.find("td", {'class':'goalfa'}).text.split(" - ")
            goals_for = goals[0]
            goals_against = goals[1]
            goal_diff = str(int(goals1) - int(goals2))

            form = team.find("td", {'class':'form'})
            form_ = form.find_all("span", {'class':'c43px'})
            form_t = ""
            for f in form_:
                form_t += f.text + " "
            
            l = [pos, team_, point, mp, wins, drawn, lost, goals_for
                , goals_against, goals_diff, form_t]

            print(" ".join(l))
        '''
        print('this function is kinda broken atm')

EPL = Search('epl', '', results=False, fixture=True)