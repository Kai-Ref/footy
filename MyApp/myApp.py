from kivy.lang import Builder
from kivymd.app import MDApp
import os
import sys
import ast
project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project)
from Database.getTables import getTables
from TicTacToe.tictactoe import TicTacToe
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.menu import MDDropdownMenu
from Configuration import Configuration


# Builder.load_file('my.kv')
class TicTacToeScreen(Screen):

	def build(self):
		pass
	
	# Define Who's turn it is
	turn = "X"
	# Keep Track of win or lose
	winner = False
	config = Configuration()
	
	# Keep track of winners and losers
	X_win = 0
	O_win = 0
	t = TicTacToe()

	league_id = None
	team_ids = config.top_teams
	exact = True
	team_combinations = t.roll_combinations(league_id, 50, team_ids, exact=exact)
	getData = getTables()
	player_df = getData.get_player_data()

	index = 0
	# load the first teams ids
	team1_id = str(team_combinations.loc[index, "Axis1"][0])
	team1_name = str(team_combinations.loc[index, "TeamsAxis1"][0])
	team2_id = str(team_combinations.loc[index, "Axis1"][1])
	team2_name = str(team_combinations.loc[index, "TeamsAxis1"][1])
	team3_id = str(team_combinations.loc[index, "Axis1"][2])
	team3_name = str(team_combinations.loc[index, "TeamsAxis1"][2])
	team4_id = str(team_combinations.loc[index, "Axis2"][0])
	team4_name = str(team_combinations.loc[index, "TeamsAxis2"][0])
	team5_id = str(team_combinations.loc[index, "Axis2"][1])
	team5_name = str(team_combinations.loc[index, "TeamsAxis2"][1])
	team6_id = str(team_combinations.loc[index, "Axis2"][2])
	team6_name = str(team_combinations.loc[index, "TeamsAxis2"][2])
	menu = None
	menu_open = False
	selected_player_id = None
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		menu_items = []
		self.menu = MDDropdownMenu(
            caller=self.ids.search_field,
            items=menu_items,
            width_mult=4,
        )

	def on_text(self, instance, text):
		if self.menu_open:
			self.menu.dismiss()
			self.menu_open = False
		if text:
			try:
				df = self.player_df[(self.player_df["players"].str.contains(text))|(self.player_df["player_href"].str.contains(text))].sort_values(by="players").reset_index(drop=True)
				menu_items = [
						{
							"text": f"{df.loc[i, 'players']} - ({df.loc[i, 'Birthday']}) [{[nationality for nationality in df.loc[i, 'nationality']]}]",
							"viewclass": "OneLineListItem",
							"on_release": lambda x= df.loc[i, 'player_id']: self.menu_callback(x),
						} for i in range(min(20, len(df)))
					]
			except Exception:
				menu_items = []
			self.menu = MDDropdownMenu(
				caller=instance,
				items=menu_items,
				width_mult=6,
				position = "bottom",
			)
			self.menu.open()
			self.menu_open = True
	
	def menu_callback(self, player_id):
		self.selected_player_id = player_id
		print(player_id)
		self.menu.dismiss()

	def build(self): # needed?
		return self.screen

	def next_combination(self):
		# maybe include random reroll of positions
		if self.index < (len(self.team_combinations)-1):
			self.index += 1
		else:
			self.team_combinations = self.t.roll_combinations(self.league_id, 50, self.team_ids, exact=self.exact)
			self.index = 0
		self.team1_id = str(self.team_combinations.loc[self.index, "Axis1"][0])
		self.team1_name = str(self.team_combinations.loc[self.index, "TeamsAxis1"][0])
		self.team2_id = str(self.team_combinations.loc[self.index, "Axis1"][1])
		self.team2_name = str(self.team_combinations.loc[self.index, "TeamsAxis1"][1])
		self.team3_id = str(self.team_combinations.loc[self.index, "Axis1"][2])
		self.team3_name = str(self.team_combinations.loc[self.index, "TeamsAxis1"][2])
		self.team4_id = str(self.team_combinations.loc[self.index, "Axis2"][0])
		self.team4_name = str(self.team_combinations.loc[self.index, "TeamsAxis2"][0])
		self.team5_id = str(self.team_combinations.loc[self.index, "Axis2"][1])
		self.team5_name = str(self.team_combinations.loc[self.index, "TeamsAxis2"][1])
		self.team6_id = str(self.team_combinations.loc[self.index, "Axis2"][2])
		self.team6_name = str(self.team_combinations.loc[self.index, "TeamsAxis2"][2])
		self.reload_team_labels()
		self.restart()

	def reload_team_labels(self):
		self.ids.lab1.text = self.team1_name
		self.ids.lab2.text = self.team2_name
		self.ids.lab3.text = self.team3_name
		self.ids.lab4.text = self.team4_name
		self.ids.lab5.text = self.team5_name
		self.ids.lab6.text = self.team6_name

	def end_game(self, a,b,c):
		self.winner = True
		a.color = "red"
		b.color = "red"
		c.color = "red"

		# Disable the buttons
		self.disable_all_buttons()

		# Set Label for winner
		#self.ids.score.text = f"{a.text} Wins!"

		# Keep track of winners and loser
		if a.text == "X":
			self.X_win = self.X_win + 1	
		else:
			self.O_win = self.O_win + 1

		self.ids.game.text = f"X Wins: {self.X_win}  |  O Wins: {self.O_win}"

	def presser(self, btn):
		if btn == self.ids.btn1:
			team_id_1 = self.team1_id
			team_id_2 = self.team4_id
		elif btn == self.ids.btn2:
			team_id_1 = self.team2_id
			team_id_2 = self.team4_id
		elif btn == self.ids.btn3:
			team_id_1 = self.team3_id
			team_id_2 = self.team4_id
		elif btn == self.ids.btn4:
			team_id_1 = self.team1_id
			team_id_2 = self.team5_id
		elif btn == self.ids.btn5:
			team_id_1 = self.team2_id
			team_id_2 = self.team5_id
		elif btn == self.ids.btn6:
			team_id_1 = self.team3_id
			team_id_2 = self.team5_id
		elif btn == self.ids.btn7:
			team_id_1 = self.team1_id
			team_id_2 = self.team6_id
			print(self.team1_name, self.team6_name)
		elif btn == self.ids.btn8:
			team_id_1 = self.team2_id
			team_id_2 = self.team6_id
			print(self.team2_name, self.team6_name)
		elif btn == self.ids.btn9:
			team_id_1 = self.team3_id
			team_id_2 = self.team6_id
			print(self.team3_name, self.team6_name)
		df = self.getData.get_combination_results(team_id_1, team_id_2)
		try:
			correct_players = df["Player IDs"][0]
			print(correct_players)
		except KeyError:
			correct_players = df["Player IDs"]
			print(correct_players)
		if str(self.selected_player_id) in correct_players:
			btn.color = "green"
			if self.turn == 'X':
				btn.text = "X"
				btn.disabled = True
				#self.ids.score.text = "O's Turn!"
				self.turn = "O"
			else:
				btn.text = "O"
				btn.disabled = True
				#self.ids.score.text = "X's Turn!"
				self.turn = "X"

			# Check To See if won
			self.win()

	
	def win(self):
		# Across
		if self.ids.btn1.text != "" and self.ids.btn1.text == self.ids.btn2.text and self.ids.btn2.text == self.ids.btn3.text:
			self.end_game(self.ids.btn1, self.ids.btn2, self.ids.btn3)

		if self.ids.btn4.text != "" and self.ids.btn4.text == self.ids.btn5.text and self.ids.btn5.text == self.ids.btn6.text:
			self.end_game(self.ids.btn4, self.ids.btn5, self.ids.btn6)

		if self.ids.btn7.text != "" and self.ids.btn7.text == self.ids.btn8.text and self.ids.btn8.text == self.ids.btn9.text:
			self.end_game(self.ids.btn7, self.ids.btn8, self.ids.btn9)
		# Down
		if self.ids.btn1.text != "" and self.ids.btn1.text == self.ids.btn4.text and self.ids.btn4.text == self.ids.btn7.text:
			self.end_game(self.ids.btn1, self.ids.btn4, self.ids.btn7)

		if self.ids.btn2.text != "" and self.ids.btn2.text == self.ids.btn5.text and self.ids.btn5.text == self.ids.btn8.text:
			self.end_game(self.ids.btn2, self.ids.btn5, self.ids.btn8)

		if self.ids.btn3.text != "" and self.ids.btn3.text == self.ids.btn6.text and self.ids.btn6.text == self.ids.btn9.text:
			self.end_game(self.ids.btn3, self.ids.btn6, self.ids.btn9)

		# Diagonal 
		if self.ids.btn1.text != "" and self.ids.btn1.text == self.ids.btn5.text and self.ids.btn5.text == self.ids.btn9.text:
			self.end_game(self.ids.btn1, self.ids.btn5, self.ids.btn9)

		if self.ids.btn3.text != "" and self.ids.btn3.text == self.ids.btn5.text and self.ids.btn5.text == self.ids.btn7.text:
			self.end_game(self.ids.btn3, self.ids.btn5, self.ids.btn7)	

	def disable_all_buttons(self):
		# Disable The Buttons
		self.ids.btn1.disabled = True
		self.ids.btn2.disabled = True
		self.ids.btn3.disabled = True
		self.ids.btn4.disabled = True
		self.ids.btn5.disabled = True
		self.ids.btn6.disabled = True
		self.ids.btn7.disabled = True
		self.ids.btn8.disabled = True
		self.ids.btn9.disabled = True

	def restart(self):
		# Reset Who's Turn It Is
		self.turn = "X"

		# Enable The Buttons
		self.ids.btn1.disabled = False
		self.ids.btn2.disabled = False
		self.ids.btn3.disabled = False
		self.ids.btn4.disabled = False
		self.ids.btn5.disabled = False
		self.ids.btn6.disabled = False
		self.ids.btn7.disabled = False
		self.ids.btn8.disabled = False
		self.ids.btn9.disabled = False

		# Clear The Buttons
		self.ids.btn1.text = ""
		self.ids.btn2.text = ""
		self.ids.btn3.text = ""
		self.ids.btn4.text = ""
		self.ids.btn5.text = ""
		self.ids.btn6.text = ""
		self.ids.btn7.text = ""
		self.ids.btn8.text = ""
		self.ids.btn9.text = ""

		# Reset The Button Colors
		self.ids.btn1.color = "green"
		self.ids.btn2.color = "green"
		self.ids.btn3.color = "green"
		self.ids.btn4.color = "green"
		self.ids.btn5.color = "green"
		self.ids.btn6.color = "green"
		self.ids.btn7.color = "green"
		self.ids.btn8.color = "green"
		self.ids.btn9.color = "green"

		# Reset The Score Label
		# self.ids.score.text = "X GOES FIRST!"

		# Reset The Winner Variable
		self.winner = False

	def get_matching_player_names(self, text):
		player_names = ["Thomas Müller", "thomas Müller", "Timmy", "Marco Friedl"]		
		matching_names = [name for name in player_names if text.lower() in name.lower()]
		self.ids.labell.text = str(matching_names)




class MyApp(MDApp):
	title = "Tic Tac Toe!"

	def build(self):
		self.theme_cls.theme_style = "Dark"
		self.theme_cls.primary_palette = "BlueGray"
		# Create the screen manager
		sm = ScreenManager()
		sm.add_widget(TicTacToeScreen(name='tictactoe'))
		# sm.add_widget(drop(name="lists"))
		return sm
		
	
if __name__ == '__main__':
    MyApp().run()