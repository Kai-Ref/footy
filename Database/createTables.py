import sqlite3
import pandas as pd
import numpy as np
import sys
import os
import ast
import requests
from tqdm import tqdm
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout
from urllib.error import HTTPError
from http.client import IncompleteRead
# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from itertools import combinations
from getTables import getTables
from WebScraping.scrapeFootyData import get_teams_all_leagues, add_all_historical_info_selected_teams, get_players_for_all_teams, get_player_info
from Configuration import Configuration
import datetime

class createTables: # alternatively fillTables
    
    def create_meta_clubs_table(config, df):
        
        
        # TODO add an check to add only new data that is different from the aready prominent data 

        # if df == None: # if no combined_df is given, then scrape the data
        #     df = get_teams_all_leagues(config, start_year=start_year)
        # determine the unique clubs within the df
        unique_df = df[["team_name", "id", "league_id"]].drop_duplicates().reset_index(drop=True)

        # check for different team_names that are stored under the same id
        if unique_df.nunique()["team_name"] != unique_df.nunique()["id"]:
           #print(unique_df.nunique())
           duplicate_list = [id for id in unique_df.id.unique() if unique_df[unique_df.id.isin([id])].nunique()["team_name"]>1]
           for id in duplicate_list:
               names = unique_df.loc[unique_df.id.isin([id]), "team_name"].unique()[-1]
               unique_df.loc[unique_df.id.isin([id]), "team_name"] = names
        # lastly remove the new duplicates
        unique_df = unique_df[["team_name", "id", "league_id"]].drop_duplicates().reset_index(drop=True)

        con = sqlite3.connect("Database/database.db")
        cur = con.cursor()
        # insert the df as a new table into our database
        unique_df.to_sql(name="meta_club_table", con=con, if_exists="replace", index=False)
        con.commit()
        cur.close()
        con.close()
    
    def create_data_clubs_table(config):
        # fill the datatable with data for each club in the meta table regrdless of their playing league (e.g. 1st or 2nd division)  

        # TODO add an check to add only new data that is different from the aready prominent data 
        # by loading in the prominent table and removing elements that are already in the to be inserted table


        # find a way to add to table instead of overhauling the entire table.... -> maybe append in combination with remove duplicates?

        # if df == None: # if no df is given, then scrape the data
        #     df = get_teams_all_leagues(config, 2000)

        # TODO Before insertion, check that the team_names are all equal to the meta_table -> maybe compare with meta table or so

        con = sqlite3.connect("Database/database.db")
        cur = con.cursor()
        # insert the df as a new table into our database
        # TODO add new_varaible that indicates if a team was in the top flight for that season
        df = get_teams_all_leagues(config, years = [year for year in range(2000,2023)])
        # needs to be 4922
        df = add_all_historical_info_selected_teams(df)
        df.to_sql(name="data_club_table", con=con, if_exists="replace", index=False)
        con.commit()
        cur.close()
        con.close()

    def create_data_player_table(config):
        con = sqlite3.connect("Database/database.db")
        cur = con.cursor()
        # query the data from all available teams
        teams_df = pd.read_sql_query(f"select * from data_club_table", con)
        # determine the unique player data for every team in teams_df
        max_retries = 5
        retry_count = 0
        # todo it could be more efficient to first determine the unique players and then scrape the data for them
        while retry_count < max_retries:
            try:
                df = get_players_for_all_teams(config, teams_df)
                break
            except (ChunkedEncodingError, ConnectionError, ReadTimeout, ValueError, IncompleteRead, HTTPError) as e:
                retry_count += 1
                print(f"Retry {retry_count}/{max_retries} - Error: {e}")
            
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                break  # Break the loop if an unrecoverable error occurs
        df.to_sql(name="data_players_table", con=con, if_exists="replace", index=False)
        con.commit()
        cur.close()
        con.close()
    
    def add_player_info_to_data_players_table(config):

        con = sqlite3.connect("Database/database.db")
        df = pd.read_sql_query(f"select * from data_players_table", con) 
        additional_df = pd.DataFrame()
        for url in tqdm(df.iloc[30000:,:].player_href, total=len(df.iloc[30000:,:])):
            additional_df = pd.concat([additional_df, get_player_info(config.base_url + url)], axis=0)
        df = pd.merge(df.loc[df.player_id.isin(additional_df.player_id), :], additional_df, on="player_id", how="left") 
        columns_with_list_type = ["transfer_years", "transfer_hrefs", "transfer_club_ids", "main_position", "other_positions", "nationality", "current_club"]
        columns_with_list_type = [column for column in columns_with_list_type if column in df.columns]
        for column in columns_with_list_type:
            df[column] = df[column].apply(lambda x: str(x))
        df.to_sql(name="data_player_table", con=con, if_exists="append", index=False)
        con.commit()
        con.close()

    def create_data_tic_tac_toe_table(meta_teams_df, df):
        # This function takes about 10 minutes

        # -> try out for the players in db
        # then check which players played for both clubs and save their player_ids as list of length 2 into a /dict
        # disregard combinations with no players
        df["club_ids"] = df["current_club"] + df["transfer_club_ids"]
        club_combinations =[]
        club_ids = meta_teams_df.id.unique()
        for club_id_1, club_id_2 in tqdm(combinations(club_ids, 2), total=len(list(combinations(club_ids, 2)))):
                # first iterate through all possible club_id combinations -> handling for retired club_id!
                if (club_id_1 != club_id_2) & (club_id_1 != config.club_id_retired) & (club_id_2 != config.club_id_retired):
                    club_1_mask = df.club_ids.apply(lambda x: club_id_1 in x)
                    club_2_mask = df.club_ids.apply(lambda x: club_id_2 in x)
                    player_ids = df.loc[club_1_mask & club_2_mask, 'player_id'].tolist()
                    if len(player_ids) > 0:
                        club_combinations.append({'Club 1': club_id_1,
                                                  'Club 2': club_id_2,
                                                  'Player IDs': player_ids
                                                  })
        club_combinations_df = pd.DataFrame(club_combinations)
        con = sqlite3.connect("Database/database.db")
        club_combinations_df["Player IDs"] = club_combinations_df["Player IDs"].apply(lambda x: str(x))
        club_combinations_df.to_sql(name="data_tic_tac_toe_table", con=con, if_exists="replace", index=False)
        con.commit()
        con.close()
        return club_combinations_df

    def create_tic_tac_toe_combinations():
        df = pd.read_sql_query(f"select * from data_tic_tac_toe_table", sqlite3.connect("Database/database.db"))
        df["Club 1"] = df["Club 1"].astype(int)
        df["Club 2"] = df["Club 2"].astype(int)
        
        unique_ids_1 = df["Club 1"].unique().tolist()
        unique_ids_2 = df["Club 2"].unique().tolist()
        unique_ids = unique_ids_1 + unique_ids_2
        unique_ids = np.unique(unique_ids).tolist()
        combinations_dict ={}
        for id in unique_ids:
            filter_index = (df["Club 2"].isin([id])) | (df["Club 1"].isin([id]))
            club_combinations_1 = df.loc[filter_index,"Club 1"].unique().tolist()
            club_combinations_2 = df.loc[filter_index,"Club 2"].unique().tolist()
            club_combinations = club_combinations_1 + club_combinations_2
            club_combinations = np.unique(club_combinations).tolist()
            if id in club_combinations:
                club_combinations.remove(id)
            combinations_dict[id] = club_combinations

        # determine all possible combinationsof 3 clubs
        intersection_list, key_list= [], []
        for key in tqdm(combinations(combinations_dict.keys(), 3), total=len(list(combinations(combinations_dict.keys(), 3)))):
            id_1, id_2, id_3 = key[0], key[1], key[2]
            intersection = set(combinations_dict[id_1]).intersection(combinations_dict[id_2], combinations_dict[id_3])
            if len(intersection) > 2:
                key_list.append(key)
                intersection_list.append(intersection)
        result_df = pd.DataFrame({"Axis 1": key_list, "Axis 2": intersection_list})
        con = sqlite3.connect("Database/database.db")
        result_df["Axis 1"]= result_df["Axis 1"].apply(lambda x: str(list(x)))
        result_df["Axis 2"]= result_df["Axis 2"].apply(lambda x: str(list(x)))
        result_df.to_sql(name="tic_tac_toe_combinations", con=con, if_exists="replace", index=False)
        con.commit()
        con.close()   
    
    def add_league_information_to_tic_tac_toe_combinations():
        """
        This function adds information of possible league exclusive combinations to the tic_tac_toe_combinations table.
        It adds the league_id to the df, which indicates the league out of which a combination is possible.
        """
        df = pd.read_sql_query(f"select * from tic_tac_toe_combinations", sqlite3.connect("Database/database.db"))
        # df= df.iloc[0:10]
        df["Axis 1"] = df["Axis 1"].apply(ast.literal_eval)
        df["Axis 2"] = df["Axis 2"].apply(ast.literal_eval)

        teams_df = pd.read_sql_query(f"select * from meta_club_table", sqlite3.connect("Database/database.db"))
        league_ids = teams_df["league_id"].unique().tolist()
        # first iterate over all defined league_ids and determine the teams that are in the league
        for league_id in league_ids:
            league_teams = teams_df.loc[teams_df["league_id"] == league_id, "id"].tolist()
            league_teams = [int(team) for team in league_teams]
            # then iterate over all combinations and check if the combination is a subset of the league_teams
            # if the combination is a subset of the league_teams, check if the intersection of the combination and the league_teams is greater than 2
            for index, row in tqdm(df.iterrows(), total=len(df)):
                if set(row["Axis 1"]).issubset(league_teams):
                    intersection = set(row["Axis 2"]) & set(league_teams)
                    # check if the intersection of the combination and the league_teams is greater than 2
                    if len(intersection) > 2:
                        df.at[index, "League ID"] = int(league_id)
                else:
                    continue
        # insert the new data into the database
        con = sqlite3.connect("Database/database.db")
        df["Axis 1"] = df["Axis 1"].apply(lambda x: str(list(x)))
        df["Axis 2"] = df["Axis 2"].apply(lambda x: str(list(x)))
        df.to_sql(name="tic_tac_toe_combinations", con=con, if_exists="replace", index=False)
        con.commit()
        con.close()

    def normalize_tic_tac_toe_tables(df=None, delete=False):
        """
        This function normalizes the tic_tac_toe_combinations table into the following tables:
        - tic_tac_toe_axis_1
        - tic_tac_toe_axis_2"""
        con = sqlite3.connect("Database/database.db")
        cursor = con.cursor()

        # Load in the previous table
        cursor.execute("SELECT * FROM tic_tac_toe_combinations")
        rows = cursor.fetchall()
        if delete:
            # Clear the data in tic_tac_toe_axis_1 table
            cursor.execute("DELETE FROM tic_tac_toe_axis_1")

            # Clear the data in tic_tac_toe_axis_2 table
            cursor.execute("DELETE FROM tic_tac_toe_axis_2")

            # Commit the changes to remove data from the tables
            con.commit()

        # Create tic_tac_toe_axis_1 table
        cursor.execute("CREATE TABLE IF NOT EXISTS tic_tac_toe_axis_1 (Axis_1_ID INTEGER PRIMARY KEY, team_1 INTEGER, team_2 INTEGER, team_3 INTEGER, League_ID INTEGER)")

        # Create tic_tac_toe_axis_2 table
        cursor.execute("CREATE TABLE IF NOT EXISTS tic_tac_toe_axis_2 (Axis_2_ID INTEGER PRIMARY KEY, team_id INTEGER, Axis_1_ID INTEGER, League_ID INTEGER)")
        
        axis_1_values = {}
        axis_2_values = {}  # Use a dictionary to keep track of (team_id, axis_1_id) pairs

        for row in tqdm(rows):
            axis_1 = ast.literal_eval(row[0])
            axis_2 = ast.literal_eval(row[1])
            if type(row[2]) == type(None):
                league_id = None
            else:
                league_id = int(row[2])

            axis_1 = tuple(axis_1)
            axis_2 = tuple(axis_2)

            # Check if the axis_1 value is already processed
            if axis_1 not in axis_1_values:
                # Get the next available Axis_1_ID
                axis_1_id = len(axis_1_values) + 1

                axis_1_values[axis_1] = axis_1_id
                team_1, team_2, team_3 = axis_1
                cursor.execute("INSERT INTO tic_tac_toe_axis_1 (Axis_1_ID, team_1, team_2, team_3, League_ID) VALUES (?, ?, ?, ?, ?)", (axis_1_id, team_1, team_2, team_3, league_id))
            else:
                axis_1_id = axis_1_values[axis_1]

            # Insert axis_2 values into tic_tac_toe_axis_2 table if the combination is not yet present
            for team_id in axis_2:
                # if (team_id, axis_1_id) not in axis_2_values:
                #     axis_2_values[(team_id, axis_1_id)] = True
                cursor.execute("INSERT INTO tic_tac_toe_axis_2 (team_id, Axis_1_ID, League_ID) VALUES (?, ?, ?)", (team_id, axis_1_id, league_id))

        # Commit the changes to insert data into the tables
        con.commit()

        # Close the connection
        con.close()



if __name__ == "__main__":
    config = Configuration()
    createTables.normalize_tic_tac_toe_tables()
    # createTables.create_data_clubs_table(config)

    # meta_teams_df = pd.read_sql_query(f"select * from meta_club_table", sqlite3.connect("Database/database.db"))
    # getTables = getTables()
    # df = getTables.get_player_data()
    # createTables.create_data_tic_tac_toe_table(meta_teams_df, df)
    # createTables.add_league_information_to_tic_tac_toe_combinations()
    # print(df.head())
    # print(df.explode("Axis 2"))