from bs4 import BeautifulSoup 
import json, re
import urllib.request
import data
import pandas as pd

#
# Currently only supports premier league games. Other leagues will be added soon
#

class Search(object):
    '''
    This uses dicts in data.py to search for Premier League Fixtures.\n
    league should ALWAYS = epl, until more are added\n
    team = 'liverpool' or 'manchestercity', all lower case\n
    leaving team blank will result in League results\n
    is results=True will show past games.\n
    if fixtures=True will show future games.\n
    Do not call aux functions as they will not work on their own.\n 
    Call the relevant function without aux
    '''
    def __init__(self, league, team, results, fixture, num_results):
        super().__init__()

        # init the variables supplied
        self.league = league
        self.team = team
        self.results = results
        self.fixture = fixture
        self.data = data.scorespro
        self.num_results = num_results
        self.detailed_data = data.premierleague
    
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
    def get_team_results_fixture_aux(self, soup, is_results, num_results):

        if is_results:
            index = 0
        else: 
            index = 1
        # find all results in the soup, index 0 == past
        results = soup.find_all("div", {'class':'compgrp'})[index]
        # find all games in the result block
        games = results.find_all("table", {'class':'blocks'})
        
        info = [[]]
        # loop over each game in the results
        for game in games:
            kick_off = game.find('td', {'class':'kick_t'}).text         # get the kick off time
            home_team = game.find('td', {'class':'home_o'}).text        # get the home team
            away_team = game.find('td', {'class':'away_o'}).text        # get the away team

            if is_results:
                score = game.find('td', {'class':'score'}).text         # if we want the score get it
            else:
                score = game.find('td', {'class': 'score'})             

                if score and not score.text == 'CANC':                  # check if the game is cancelled
                    score = '-'
                else:
                    score = 'CANC'
            
            info.append([kick_off, home_team, score, away_team])   # add data scraped to data to be added to frame
        
        df = pd.DataFrame(info, columns = ['KoT', 'Home', 'Score', 'Away'])    # create the df
        df = df.iloc[1:]                                                                    # dont need the top row
        return df.iloc[:self.num_results]
            
    def get_team_results_fixture(self):
        '''
        Get the results and/or fixtures for the given team.
        If we want results, it runs the aux func returning past fixtures
        If not, it gets future fixtures
        Returns a pandas dataframe
        '''
        team = self.team
        league = self.league
        num_results = self.num_results

        url = self.data[league][team]
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        if self.results:
            df = self.get_team_results_fixture_aux(soup, True, num_results)
        else:
            df = self.get_team_results_fixture_aux(soup, False, num_results)
        
        return df
    
    def get_team_detailed_info(self):
        '''
        Returns a list of:
        Top Scorer Name, Top Scorer Goals, Team Unbeaten Streak, Team Total Goals, Team Av Goals/Game, 
        Team Shots Total, Team Shots on Target, Team Shot Accuracy, Penalty Goals, Big Chances Created, Times hit the woodwork, 
        Team Total Passes
        '''
        team = self.team
        league = self.league
        info = []

        # using scorespro
        url = self.data[league][team]
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        # find top scorer block
        top_scorer_a = soup.find("div", {'class':'topscorerInfo'})
        top_scorer_name = top_scorer_a.find('div', {'class':'sp-teamtopscorer_name'}).text
        top_scorer_goals = self.convert_to_int(top_scorer_a.find(
                                            'div', {'class':'sp-teamtopscorer_totalgoals'}).text)   # top goalscorer is found here

        # find unbeaten streak
        unbeaten_streak_str = soup.find("div", {'class':'act_comp_unbeat'}).text
        unbeaten_streak_int = re.sub('\D', '', unbeaten_streak_str)
        #info.append([top_scorer_name, top_scorer_goals, unbeaten_streak_int])

        # now switch to offical prem stats
        url = self.detailed_data[team]
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        stat_block = soup.find('ul', {'class':'normalStatList'})
        #for stat_block in stat_blocks:
        # could maybe loop over these rather than converting them all here
        goals_total = self.convert_to_int(stat_block.find('span', {'class':'statgoals'}).text)      # find the goals scored stat
        goals_per_game = self.convert_to_int(stat_block.find('span', {'class':'statgoals_per_game'}).text)
        goals_per_game = goals_per_game / 100       # bc convert_to_int wont return the '.' in the number
        shots_total = self.convert_to_int(stat_block.find('span', {'class':'stattotal_scoring_att'}).text)
        shots_ot_total = self.convert_to_int(stat_block.find('span', {'class':'statontarget_scoring_att'}).text)
        shot_accuracy = self.convert_to_int(stat_block.find('span', {'class':'statshot_accuracy'}).text)
        pen_goals = self.convert_to_int(stat_block.find('span', {'class':'statatt_pen_goal'}).text)
        chances_created = self.convert_to_int(stat_block.find('span', {'class':'statbig_chance_created'}).text)
        hit_woodwork = self.convert_to_int(stat_block.find('span', {'class':'stathit_woodwork'}).text)
        total_passes = self.convert_to_int(stat_block.find('span', {'class':'stattotal_pass'}).text)

        info.append([top_scorer_name, top_scorer_goals, unbeaten_streak_int, goals_total, goals_per_game, 
                    shots_total, shots_ot_total, shot_accuracy, pen_goals, chances_created, hit_woodwork, 
                    total_passes])
     
        return info

    def convert_to_int(self, string):
        return int(''.join(filter(str.isdigit, string)))

    # another helper func for searching for an entire leagues results
    # prints off the previous rounds based on limit
    def get_league_results_fixture_aux(self, soup):
        results = soup.find('div', {'id':'national'})
        rounds = results.find_all(True, {'class':['ncet', 'blocks']})

        info = [[]]
        num_rounds = 0
        for line in rounds:
            round_ = line.find('li', {'class':'ncet_round'})
            if round_:
                num_rounds += 1
                if num_rounds > self.num_results:
                    break
            else:
                game = line.find('tbody')
                kick_off_date = game.find('span', {'class':'kick_t_dt'}).text
                kick_off_time = game.find('span', {'class':'kick_t_ko'}).text
                home_team = game.find('td', {'class':'home'}).text
                away_team = game.find('td', {'class':'away'}).text
                score = game.find('td', {'class':'score'}).text
                
                info.append([kick_off_date, kick_off_time, home_team, score, away_team])
        
        df = pd.DataFrame(info, columns = ['Date', 'Time', 'Home', 'Score', 'Away'])    # create the df
        df = df.iloc[1:]                                                                    # dont need the top row
        return df.iloc[:self.num_results]
    

    def get_league_results_fixture(self):
        '''
        Calls the correct helper function for the input
        '''
        league = self.league

        if self.results:
            url = self.data[league]['_l_name_r']
            html = self.get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            df = self.get_league_results_fixture_aux(soup)
        
        if self.fixture:
            url = self.data[league]['_l_name_f']
            html = self.get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            df = self.get_league_results_fixture_aux(soup)
        
        return df
    
    def get_league_table(self):
        '''
        Returns a pandas df of the current premier league table
        '''
        league = self.league
        url = self.data[league]['_l_name_t']
        
        teams = pd.read_html(url)

        # this removes unneccesary columns 
        df = teams[0].iloc[:, 1:-1]

        # convert the first row to the header
        nh = df.iloc[0]     # select the first row
        df = df.iloc[1:]    # grab the df without the first row
        df.columns = nh     # add the new header
        # return the top rows of the df based on num results
        return df.iloc[:self.num_results]
    
    def get_league_top_scorers(self):
        league = self.league
        url = self.data[league]['_l_name_s']
   
        
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        results = soup.find_all('div', {'class':'tsl_row'})
        #rows = results.find_all('div', {'class':'tsl_row'})

        info = [[]]
        rank_ = 0
        for result in results:
            rank = result.find('div', {'class':'tsl_rank'}).text
            if rank == '-':
                rank = rank_
            else:
                rank_ = rank
            player = result.find('div', {'class':'tsl_player'}).text
            team = result.find('div', {'class':'tsl_team'}).text
            goals = result.find('div', {'class':'tsl_goals'}).text
            pens = result.find('div', {'class':'tsl_pen'}).text
            assists = result.find('div', {'class':'tsl_assist'}).text

            info.append([rank, player, team, goals, pens, assists])
        
        df = pd.DataFrame(info, columns=['Rank', 'Player', 'Team', 'Goals', 'Pens', 'Assists'])
        df = df.iloc[1:] 

        return df.iloc[:self.num_results]
        

test_search = Search('epl', 'liverpool', results=True, fixture=False, num_results=100)

detailed = test_search.get_team_results_fixture()

print(detailed)

#top_scorers = test_search.get_league_top_scorers()
#top_liverpool_scorer = top_scorers.loc[top_scorers['Team']=='Liverpool']
#print (top_liverpool_scorer['Player'].values)
#print (top_liverpool_scorer['Goals'].values)