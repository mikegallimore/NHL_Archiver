# -*- coding: utf-8 -*-
"""
@author: @mikegallimore
"""

import requests
import os
import csv
import json
import pandas as pd
import dict_teams
import parameters
from bs4 import BeautifulSoup
import re

def escape_xml_illegal_chars(unicodeString, replaceWith=u'?'):
	return re.sub(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', replaceWith, unicodeString)

def parse_ids(season_id, game1, game2):

    # pull common variables from the parameters file
    files_root = parameters.files_root
   
    # team- and season-specific filepaths
    season_root = season_id + '/'
      
    if not os.path.exists(season_root):
        os.makedirs(season_root)
        print('Created subfolder ' + season_root)    

    files_path = season_root + 'Files/'
    
    if not os.path.exists(files_path):
        os.makedirs(files_path)
        print('Created subfolder ' + files_path)

    # retrieve schedule
    schedule_csv = files_root + season_id + '_schedule.csv'
    schedule_exists = os.path.isfile(schedule_csv)
    
    if schedule_exists:
        print(season_id + ' schedule already exists')
        
    else:
        JSON_schedule = season_root + season_id + '_schedule.json'
        schedule_csv = season_root + season_id + '_schedule.csv'
		
		# find the .json schedule source and save to file
        try:
            year_start = season_id[0:4]
            year_end = season_id[4:8]
            if int(season_id) != 20192020 or int(season_id) != 20202021:
                JSON_schedule_url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=' + year_start + '-08-30&endDate=' + year_end + '-06-30'
            if int(season_id) == 20192020:
                JSON_schedule_url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=' + year_start + '-08-30&endDate=' + year_end + '-10-30'
            if int(season_id) == 20202021:
                JSON_schedule_url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=' + year_end + '-01-01&endDate=' + year_end + '-07-30'
            
            JSON_schedule_request = requests.get(JSON_schedule_url, timeout=5).text
            
            f = open(season_root + season_id + '_schedule.json', 'w+')
            f.write(JSON_schedule_request)
            f.close()
            print('Retrieved NHL schedule (JSON) for ' + season_id)
        except:
            print('ERROR: Could not retreive the season schedule (JSON) for ' + season_id)
			
		# pull and parse the .json schedule file as .csv
        with open(JSON_schedule) as JSON_schedule_in:
            JSON_schedule_parsed = json.load(JSON_schedule_in)
        
            JSON_game_dates = JSON_schedule_parsed['dates']
                       
            # begin the portion of the script that handles the csv generation
            with open(schedule_csv, 'w', newline='') as schedule_out:
                JSON_csvWriter = csv.writer(schedule_out)
                
                JSON_csvWriter.writerow(['SEASON', 'GAME_ID', 'DATE', 'HOME', 'AWAY', 'STATUS'])
                
                for JSON_allgames in JSON_game_dates:
                    JSON_dates = JSON_allgames['date']
                
                    JSON_games = JSON_allgames['games']
                
                    for JSON_game in JSON_games:
        
                        JSON_seasonid = JSON_game['season']
                
                        JSON_game_id = str(JSON_game['gamePk'])[5:]
                        JSON_game_id = int(JSON_game_id)
        
                        if JSON_game_id > 39999:
                            continue
        
                        JSON_date = JSON_dates
                        JSON_date_split = JSON_date.split('-')
                        JSON_year = JSON_date_split[0]
                        JSON_month = JSON_date_split[1]
                        JSON_day = JSON_date_split[2]
                        JSON_date = JSON_month + '/' + JSON_day + '/' + JSON_year
                         
                        JSON_home = JSON_game['teams']['home']['team']['name'].upper()
                        JSON_away = JSON_game['teams']['away']['team']['name'].upper()                  

                        JSON_status = JSON_game['status']['detailedState']
                                        
                        JSON_game_data = (JSON_seasonid, JSON_game_id, JSON_date, JSON_home, JSON_away, JSON_status)
                           
                        ### write the rows of shifts to the csv file
                        JSON_csvWriter.writerows([JSON_game_data])

        try:
			# reload the newly minted .csv file to replace the team names with their tricodes
            schedule_df = pd.read_csv(schedule_csv)
            
            schedule_df = schedule_df[(schedule_df.GAME_ID < 40000)].sort_values('GAME_ID')
            schedule_df['AWAY'] = schedule_df['AWAY'].replace(dict_teams.NHL)
            schedule_df.loc[schedule_df['AWAY'].str.contains('CANADIENS'), 'AWAY'] = 'MTL'

            schedule_df['HOME'] = schedule_df['HOME'].replace(dict_teams.NHL)
            schedule_df.loc[schedule_df['HOME'].str.contains('CANADIENS'), 'HOME'] = 'MTL'
            
            schedule_df.to_csv(schedule_csv, index = False)
            
        except:
			# reload the newly minted .csv file to replace the team names with their tricodes
            schedule_df = pd.read_csv(schedule_csv, encoding='latin-1')
            
            schedule_df = schedule_df[(schedule_df.GAME_ID < 40000)].sort_values('GAME_ID')
            schedule_df['AWAY'] = schedule_df['AWAY'].replace(dict_teams.NHL)
            schedule_df.loc[schedule_df['AWAY'].str.contains('CANADIENS'), 'AWAY'] = 'MTL'

            schedule_df['HOME'] = schedule_df['HOME'].replace(dict_teams.NHL)
            schedule_df.loc[schedule_df['HOME'].str.contains('CANADIENS'), 'HOME'] = 'MTL'
            
            
            schedule_df.to_csv(schedule_csv, index = False)

        print('Finished parsing the NHL schedule for ' + season_id)

    # reload the season's schedule as a dataframe; filter for completed games; create a list containing just the game ids
    schedule_df = pd.read_csv(schedule_csv)

    final_df = schedule_df['STATUS'] == 'Final'
    final_df = schedule_df[final_df]
    
    ids_df = final_df.copy()
    ids_df = ids_df.drop(columns=['SEASON', 'DATE', 'HOME', 'AWAY', 'STATUS'])
    game_ids_list = ids_df['GAME_ID'].values.tolist()

    # set paths to retrieve HTM files
    ROS_path = files_path + 'HTM/ROS/'
    PBP_path = files_path + 'HTM/PBP/'
    TH0_path = files_path + 'HTM/TH0/'
    TV0_path = files_path + 'HTM/TV0/'

    # set paths to retrieve JSON files
    livefeed_path = files_path + 'JSON/LiveFeed/'
    shifts_path = files_path + 'JSON/Shifts/'

    # set path to retrieve TXT files
    ESPN_scoreboard_path = files_path + 'TXT/ESPN/'

    # set path to retrieve XML files
    ESPN_pbp_path = files_path + 'XML/ESPN/'

    # create fetched HTM folders if they do not already exist
    if not os.path.exists(ROS_path):
        os.makedirs(ROS_path)
        print('Created subfolder ' + ROS_path)  
    if not os.path.exists(PBP_path):
        os.makedirs(PBP_path)
        print('Created subfolder ' + PBP_path)
    if not os.path.exists(TH0_path):
        os.makedirs(TH0_path)
        print('Created subfolder ' + TH0_path)
    if not os.path.exists(TV0_path):
        os.makedirs(TV0_path)
        print('Created subfolder ' + TV0_path)
    
    # create fetched JSON folders if they do not already exist
    if not os.path.exists(livefeed_path):
        os.makedirs(livefeed_path)
        print('Created subfolder ' + livefeed_path)  
    if not os.path.exists(shifts_path):
        os.makedirs(shifts_path)
        print('Created subfolder ' + shifts_path) 

    # create fetched TXT folders if they do not already exist
    if not os.path.exists(ESPN_scoreboard_path):
        os.makedirs(ESPN_scoreboard_path)
        print('Created subfolder ' + ESPN_scoreboard_path)
  
    # create fetched XML folders if they do not already exist
    if not os.path.exists(ESPN_pbp_path):
        os.makedirs(ESPN_pbp_path)
        print('Created subfolder ' + ESPN_pbp_path)

    # determine whether to fetch files for a specific game, range of games or any final games missing from the fetched folders
    if game1 is not None and game2 is None:
        game1 = int(game1)
        single_list = [game1]
        single_list_filtered = [x for x in single_list if x in game_ids_list]       

        # HTM
        ROS_fetch = single_list_filtered
        PBP_fetch = single_list_filtered                
        TH0_fetch = single_list_filtered                
        TV0_fetch = single_list_filtered                

        # JSON
        livefeed_fetch = single_list_filtered             
        shifts_fetch = single_list_filtered                

        # XML
        ESPN_fetch = single_list_filtered

    if game1 is not None and game2 is not None:
        game1 = int(game1)
        game2 = int(game2)
        multi_list = list(range(game1, game2+1))
        multi_list_filtered = [x for x in multi_list if x in game_ids_list]
        
        # HTM
        ROS_fetch = multi_list_filtered
        PBP_fetch = multi_list_filtered
        TH0_fetch = multi_list_filtered
        TV0_fetch = multi_list_filtered
    
        # JSON
        livefeed_fetch = multi_list_filtered
        shifts_fetch = multi_list_filtered

        # XML
        ESPN_fetch = multi_list_filtered
    
    if game1 is None and game2 is None:
        final_list = game_ids_list

        # HTM
        ROS_fetched = os.listdir(ROS_path)
        ROS_all = [season_id + '_' + str(id) + '_rosters.HTM' for id in final_list]
        ROS_missing = [x for x in ROS_all if x not in ROS_fetched]
        ROS_fetch = ROS_missing

        PBP_fetched = os.listdir(PBP_path)
        PBP_all = [season_id + '_' + str(id) + '_pbp.HTM' for id in final_list]
        PBP_missing = [x for x in PBP_all if x not in PBP_fetched]
        PBP_fetch = PBP_missing

        TH0_fetched = os.listdir(TH0_path)
        TH0_all = [season_id + '_' + str(id) + '_shifts_home.HTM' for id in final_list]
        TH0_missing = [x for x in TH0_all if x not in TH0_fetched]
        TH0_fetch = TH0_missing

        TV0_fetched = os.listdir(TV0_path)
        TV0_all = [season_id + '_' + str(id) + '_shifts_away.HTM' for id in final_list]
        TV0_missing = [x for x in TV0_all if x not in TV0_fetched]
        TV0_fetch = TV0_missing

        # JSON
        livefeed_fetched = os.listdir(livefeed_path)
        livefeed_all = [season_id + '_' + str(id) + '_livefeed.json' for id in final_list]
        livefeed_missing = [x for x in livefeed_all if x not in livefeed_fetched]
        livefeed_fetch = livefeed_missing

        shifts_fetched = os.listdir(shifts_path)
        shifts_all = [season_id + '_' + str(id) + '_shifts.json' for id in final_list]
        shifts_missing = [x for x in shifts_all if x not in shifts_fetched]
        shifts_fetch = shifts_missing

        # XML
        ESPN_fetched = os.listdir(ESPN_pbp_path)
        ESPN_all = [season_id + '_' + str(id) + '_ESPN_pbp.xml' for id in final_list]
        ESPN_missing = [x for x in ESPN_all if x not in ESPN_fetched]
        ESPN_fetch = ESPN_missing
        
    ###
    ### FETCH .HTM GAMEFILES
    ###

    #
    # Rosters
    #

    # begin loop
    for id in ROS_fetch:
        
        # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched rosters folder
        if game1 is not None and game2 is None:
            game_id = str(id)
        if game1 is not None and game2 is not None:
            game_id = str(id)   
        if game1 is None and game2 is None:          
            game_id = str(id).split('_')[1]
        
        try:
            ROS_content = requests.get('http://www.nhl.com/scores/htmlreports/' + season_id + '/RO0' + game_id + '.HTM', timeout=5).text
            if(len(ROS_content) < 10000):
                raise Exception
            f = open(ROS_path + season_id + '_' + game_id + '_rosters.HTM', 'w+')
            f.write(ROS_content)
            f.close()
            print('Retrieved NHL rosters (.HTM) for ' + season_id + ' ' + game_id)
        except:
            print('ERROR: Could not retrieve NHL rosters (.HTM) for ' + season_id + ' ' + game_id)
                
    #
    # Play-by-Play
    #

    # begin loop
    for id in PBP_fetch:

        # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched play-by-play folder
        if game1 is not None and game2 is None:
            game_id = str(id)
        if game1 is not None and game2 is not None:
            game_id = str(id)        
        if game1 is None and game2 is None:          
            game_id = str(id).split('_')[1]
        
        try:
            PBP_content = requests.get('http://www.nhl.com/scores/htmlreports/' + season_id + '/PL0' + game_id + '.HTM', timeout=5).text
            if(len(PBP_content) < 10000):
                raise Exception
            f = open(PBP_path + season_id + '_' + game_id + '_pbp.HTM', 'w+')
            f.write(PBP_content)
            f.close()
            print('Retrieved NHL play-by-play (.HTM) for ' + season_id + ' ' + game_id)
        except:
            print('ERROR: Could not retrieve NHL play-by-play (.HTM) for ' + season_id + ' ' + game_id)

    #
    # Home Shifts
    #
 
    # begin loop
    for id in TH0_fetch:

        # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched home shifts folder
        if game1 is not None and game2 is None:
            game_id = str(id)
        if game1 is not None and game2 is not None:
            game_id = str(id)      
        if game1 is None and game2 is None:          
            game_id = str(id).split('_')[1]
        
        try:
            TH0_content = requests.get('http://www.nhl.com/scores/htmlreports/' + season_id + '/TH0' + game_id + '.HTM', timeout=5).text
            if(len(TH0_content) < 10000):
                raise Exception
            f = open(TH0_path + season_id + '_' + game_id + '_shifts_home.HTM', 'w+')
            f.write(TH0_content)
            f.close()
            print('Retrieved NHL shifts (TH0, .HTM) for ' + season_id + ' ' + game_id)
        except:
            print('ERROR: Could not retrieve NHL shifts (TH0, .HTM) for ' + season_id + ' ' + game_id)

    #
    # Away Shifts
    #     

    # begin loop
    for id in TV0_fetch:

        # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched away shifts folder
        if game1 is not None and game2 is None:
            game_id = str(id)
        if game1 is not None and game2 is not None:
            game_id = str(id)    
        if game1 is None and game2 is None:          
            game_id = str(id).split('_')[1]

        try:
            TV0_content = requests.get('http://www.nhl.com/scores/htmlreports/' + season_id + '/TV0' + game_id + '.HTM', timeout=5).text
            if(len(TV0_content) < 10000):
                raise Exception
            f = open(TV0_path + season_id + '_' + game_id + '_shifts_away.HTM', 'w+')
            f.write(TV0_content)
            f.close()
            print('Retrieved NHL shifts (TVI, .HTM) for ' + season_id + ' ' + game_id)
        except:
            print('ERROR: Could not retrieve NHL shifts (TV0, .HTM) for ' + season_id + ' ' + game_id)


    ###
    ### FETCH .JSON GAMEFILES
    ###

    #
    # LiveFeed
    #

    # begin loop
    for id in livefeed_fetch:

        # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched livefeed folder
        if game1 is not None and game2 is None:
            game_id = str(id)
        if game1 is not None and game2 is not None:
            game_id = str(id)       
        if game1 is None and game2 is None:          
            game_id = str(id).split('_')[1]

        try:
            JSON_content = requests.get('http://statsapi.web.nhl.com/api/v1/game/' + season_id[0:4] + '0' + game_id + '/feed/live', timeout=5).text
            if(len(JSON_content) < 1000):
                raise Exception
            f = open(livefeed_path + season_id + '_' + game_id + '_livefeed.json', 'w+')
            f.write(JSON_content)
            f.close()
            print('Retrieved NHL livefeed (.JSON) for ' + season_id + ' ' + game_id)
        except:
            print('ERROR: Could not retrieve NHL livefeed (.JSON) ' + season_id + ' ' + game_id)

    #
    # Shifts
    #
    
    if int(season_id) >= 20102011:
        
        # begin loop
        for id in shifts_fetch:

            # set the game_id value contingent on whether a specific game, range of games or any final games missing from the fetched JSON shifts folder
            if game1 is not None and game2 is None:
                game_id = str(id)
            if game1 is not None and game2 is not None:
                game_id = str(id)        
            if game1 is None and game2 is None:           
                game_id = str(id).split('_')[1]    
            
            try:
                JSON_content = requests.get('https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId=' + season_id[0:4] + '0' + game_id, timeout=5).text
                if(len(JSON_content) < 1000):
                    raise Exception
                f = open(shifts_path + season_id + '_' + game_id + '_shifts.json', 'w+')
                f.write(JSON_content)
                f.close()
                print('Retrieved NHL shifts (.JSON) for ' + season_id + ' ' + game_id)
            except:
                print('ERROR: Could not retrieve NHL shifts (.JSON) for ' + season_id + ' ' + game_id)

                
    ###
    ### FETCH .TXT & .XML GAMEFILES (ESPN)
    ###
               
    #
    # Scoreboard
    #
                
    # begin loop
    for id in ESPN_fetch:
        game_id = str(id)
        
        ESPN_df = final_df.copy()
        ESPN_df = ESPN_df[(ESPN_df['GAME_ID']) == id]
        date = ESPN_df['DATE'].to_string(index=False)
        ESPN_df['DATE'] = ESPN_df['DATE'].str.replace('/','-')

        ESPN_date_df = ESPN_df['DATE'].str.split('-', n = 3, expand = True)

        ESPN_year = ESPN_date_df[2].to_string(index=False)
        ESPN_month_no = ESPN_date_df[0].to_string(index=False)
        ESPN_day_no = ESPN_date_df[1].to_string(index=False)

        home = ESPN_df['HOME'].to_string(index=False)
        away = ESPN_df['AWAY'].to_string(index=False)

        # retrieve the ESPN scoreboard HTML
        ESPN_scoreboard_file = ESPN_scoreboard_path + ESPN_year + '_' + ESPN_month_no + '_' + ESPN_day_no + '_' + 'ESPN_scoreboard.txt'
        try:
            if ESPN_scoreboard_file in ESPN_scoreboard_path:
                pass
            elif ESPN_scoreboard_file not in ESPN_scoreboard_path:
                ESPN_scoreboard = requests.get('https://www.espn.com/nhl/scoreboard/_/date/' + ESPN_year + ESPN_month_no + ESPN_day_no, timeout=5).text
                f = open(ESPN_scoreboard_file, 'w+')
                f.write(ESPN_scoreboard)
                f.close()
                print('Retrieved the ESPN scoreboard (.TXT) for ' + season_id + ' ' + game_id)

        except:
            print('Could not retrieve the ESPN scoreboard (.TXT) for ' + season_id + ' ' + game_id)

        #
        # Play-by-Play
        #
            
        # use the scoreboard HTML to retrieve the ESPN play-by-play
        with open(ESPN_scoreboard_file, 'r') as get_ESPN_scoreboard:
            ESPN_soup = BeautifulSoup(get_ESPN_scoreboard, 'html.parser')
   
            ESPN_teams_divs = ESPN_soup.find_all('div', {'class': 'ScoreCell__TeamName ScoreCell__TeamName--shortDisplayName truncate db'})

            ESPN_teams = [i.get_text() for i in ESPN_teams_divs]
            ESPN_teams = [ESPN_teams[i:i+2] for i in range(0, len(ESPN_teams), 2)]
          
            ESPN_teams_df = pd.DataFrame(ESPN_teams, columns=['AWAY', 'HOME'])

            ESPN_ids_links = ESPN_soup.find_all('a', {'class': 'AnchorLink Button Button--sm Button--anchorLink Button--alt mb4 w-100'}, href=True)

            ESPN_ids = [i['href'] for i in ESPN_ids_links]

            ESPN_ids = [ESPN_ids[i:i+2] for i in range(0, len(ESPN_ids), 2)]
            ESPN_ids = [i[0].rsplit('/', 1)[1] for i in ESPN_ids]

            ESPN_ids_unique=[]
            [ESPN_ids_unique.append(i) for i in ESPN_ids if i not in ESPN_ids_unique]

            ESPN_ids_df = pd.DataFrame(ESPN_ids_unique, columns=['ESPN_ID'])          
           
            ESPN_ids_df = pd.concat([ESPN_ids_df, ESPN_teams_df], axis=1)
            if int(season_id) >= 20142015:
                ESPN_ids_df['HOME'] = ESPN_ids_df['HOME'].replace(dict_teams.MONIKERS_DICT)
                ESPN_ids_df['AWAY'] = ESPN_ids_df['AWAY'].replace(dict_teams.MONIKERS_DICT)
            elif int(season_id) < 20142015 and int(season_id) >= 20112012:
                ESPN_ids_df['HOME'] = ESPN_ids_df['HOME'].replace(dict_teams.MONIKERS_DICT_PHX)
                ESPN_ids_df['AWAY'] = ESPN_ids_df['AWAY'].replace(dict_teams.MONIKERS_DICT_PHX)
            elif int(season_id) < 20112012:
                ESPN_ids_df['HOME'] = ESPN_ids_df['HOME'].replace(dict_teams.MONIKERS_DICT_WPG2ATL)
                ESPN_ids_df['AWAY'] = ESPN_ids_df['AWAY'].replace(dict_teams.MONIKERS_DICT_WPG2ATL)
                       
            ESPN_id_df = ESPN_ids_df.copy()
            ESPN_id_df = ESPN_id_df[(ESPN_id_df['HOME'] == home) & (ESPN_id_df['AWAY'] == away)]
            try:
                ESPN_id = ESPN_id_df['ESPN_ID'].values[0]
            except:
                ESPN_id_dict = {}
                if int(season_id) >= 20142015:                
                    ESPN_id_dict = {'BOS': '01', 'BUF': '02', 'CGY': '03', 'CHI': '04', 'DET': '05', 'EDM': '06', 'CAR': '07', 'LAK': '08', 'DAL': '09', 'MTL': '10', 'NJD': '11', 'NYI': '12', 'NYR': '13', 'OTT': '14', 'PHI': '15', 'PIT': '16', 'COL': '17', 'SJS': '18', 'STL': '19', 'TBL': '20', 'TOR': '21', 'VAN': '22', 'WSH': '23', 'ARI': '24', 'ANA': '25', 'FLA': '26', 'NSH': '27', 'WPG': '28', 'CBJ': '29', 'MIN': '30', 'VGK': '31'}                   
                if int(season_id) >= 20112012 and int(season_id) <= 20132014:
                    ESPN_id_dict = {'BOS': '01', 'BUF': '02', 'CGY': '03', 'CHI': '04', 'DET': '05', 'EDM': '06', 'CAR': '07', 'LAK': '08', 'DAL': '09', 'MTL': '10', 'NJD': '11', 'NYI': '12', 'NYR': '13', 'OTT': '14', 'PHI': '15', 'PIT': '16', 'COL': '17', 'SJS': '18', 'STL': '19', 'TBL': '20', 'TOR': '21', 'VAN': '22', 'WSH': '23', 'PHX': '24', 'ANA': '25', 'FLA': '26', 'NSH': '27', 'WPG': '28', 'CBJ': '29', 'MIN': '30'}                                    
                if int(season_id) <= 20102011:
                    ESPN_id_dict = {'BOS': '01', 'BUF': '02', 'CGY': '03', 'CHI': '04', 'DET': '05', 'EDM': '06', 'CAR': '07', 'LAK': '08', 'DAL': '09', 'MTL': '10', 'NJD': '11', 'NYI': '12', 'NYR': '13', 'OTT': '14', 'PHI': '15', 'PIT': '16', 'COL': '17', 'SJS': '18', 'STL': '19', 'TBL': '20', 'TOR': '21', 'VAN': '22', 'WSH': '23', 'PHX': '24', 'ANA': '25', 'FLA': '26', 'NSH': '27', 'ATL': '28', 'CBJ': '29', 'MIN': '30'}
                
                ESPN_id_locationcode = ESPN_id_dict[home]

                ESPN_id_yearcode = str()
                if int(season_id) == 20062007:
                    ESPN_id_yearcode = '26'
                if int(season_id) == 20072008:
                    ESPN_id_yearcode = '27'
                if int(season_id) == 20082009:
                    ESPN_id_yearcode = '28'
                if int(season_id) == 20092010:
                    ESPN_id_yearcode = '29'                    
                if int(season_id) == 20102011:
                    ESPN_id_yearcode = '30'
                    
                ESPN_id = ESPN_id_yearcode + date.split('/')[0] + date.split('/')[1] + '0' + ESPN_id_locationcode

            # retrieve ESPN's play-by-play (XML) data using ESPN_id; scrub potential illegal characters (https://bugs.python.org/issue5166)
            try:
                ESPN_url = 'http://www.espn.com/nhl/gamecast/data/masterFeed?lang=en&isAll=true&gameId=' + str(ESPN_id)
                ESPN_content = requests.get(ESPN_url, timeout=5).text
                f = open(ESPN_pbp_path + season_id + '_' + game_id + '_' + 'pbp_ESPN.xml', 'w+')
                f.write(escape_xml_illegal_chars(ESPN_content))
                f.close()
                print('Retrieved the ESPN play-by-play (.XML) for ' + season_id + ' ' + game_id)
            except:
                print('ERROR: Could not retrieve the ESPN play-by-play (.XML) for ' + season_id + ' ' + game_id)
