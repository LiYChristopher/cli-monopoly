from models import *

class Engine(object):
	def __init__(self, num_players, board=Board(DEFAULT_TILES, None), 
				 cards=Cards(CHANCE, COMMUNITY_CHEST)):
		self.num_players = num_players
		self.players = {}
		self.board = board
		self.bank = Bank(board, self.players)
		self.cards = cards
		self.turns = 0

	def setup(self):
		''' Factory method that sets up Player objects, and essential
		in-game properties like bank balances. '''

		# creates all players
		for player in range(1, self.num_players+1):
			name = raw_input("What's your name player? > ")
			self.players[name] = Player(name, self.board, self.cards)
		# includes name of other players, for future interaction purposes
		for player in self.players.values():
			player.others = [other for other in self.players.values() if other != player]
			print "Player %s has been added to game." % (player.name)
		self.cards.shuffle_cards()
		# set up interactor
		Interactor.players = self.players
		Interactor.board = self.board
		Interactor.bank = self.bank
		Interactor.cards = self.cards
		Interactor.db = dbInterface()
		print 'Interactor Initialized!'
		# set up game logger
		gameLogger.players = self.players
		gameLogger.player_logs = { p : [] for p in self.players }
		print 'Game logger initialized!'

		return 

	def turn(self):
		''' Advances game state - orchestrates a turn for each player using 
		the Player.roll_dice() method.'''

		for player in self.players.values():
			print 
			print "%s, it's your turn now!" % player.name
			current_location = player.roll_dice(self.board, self.bank, self.cards)
			if current_location != None:
				player.interact(current_location, self.board, self.bank, self.cards)
			player.check_monopoly()
			self.bank.update_all_rents(self.players)
			gameLogger.push_public_logs()
		self.turns += 1		
		return

	def summary(self):
		print "________________"
		print '%s turns have elapsed in this game so far.' % self.turns
		for player in self.players.values():
			print "Player: ", player.name
			print "Money: $", player.money
			property_display = [p.name for p in player.properties.values()]
			print "Monopolies: ", player.check_monopoly()
			print "Property: ", property_display
		print "Total Transactions by Bank (Dollars): $", self.bank.total


if __name__ == '__main__':
	import random

	game = Engine(3)
	game.setup()
	random_player = random.choice(game.players.values())
	for i in range(17):
#		print "You currently have ... $%s", test_player.money
		print "Your current position is....", game.board.layout[random_player.position] 
		random_player.interact_card(game.cards, game.board, game.bank, 'Chance')
	pass

'''	for turn in range(0, 10):
		game.turn()

	game.summary()'''
	
	