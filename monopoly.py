
''' Game Engine.
which intializes essential game elements, and
coordinates them. These elements include mechanics like turns,
as well as game state updates (like for rent or logs).
'''

from models import Board, Cards, Bank, Player
from models import DbInterface
from config import DEFAULT_TILES
from models import Interactor
from models import GameLogger


class Monopoly(object):
	''' This is the game engine.

		:num_players: - number of players in game (see command-line interface.)
		:turns: - number of turns in game (see command-line interface.)
		:board: - by default, Board object using standard tiles.
		:cards: - by default, Cards object using standard game cards.
	'''

	def __init__(self, num_players, board=Board(DEFAULT_TILES), cards=Cards()):
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
		Interactor.db = DbInterface()
		print 'Interactor Initialized!'
		# set up game logger
		GameLogger.players = self.players
		GameLogger.player_logs = {p: [] for p in self.players}
		print 'Game logger initialized!'
		return "Setup complete"

	def turn(self):
		''' Advances game state - orchestrates a turn for each player using
		the Player.roll_dice() method.'''

		for player in self.players.values():
			print "\n%s, it's your turn now!" % player.name
			current_location = player.roll_dice(self.board, self.bank)
			if current_location is not None:
				player.interact(current_location, self.board, self.bank, self.cards)
			player.check_monopoly()
			self.bank.update_all_rents(self.players)
			GameLogger.push_public_logs()
		msg = "\n -- End of Turn %s. \n" % self.turns
		GameLogger.add_log(msgtype='basic', msg=msg)
		self.turns += 1
		return

	def play(self, turns):
		''' Runs the game, following setup, for a duration specified by
		the command-line argument, 't' (50 by default).'''

		for _ in range(turns):
			self.turn()
		return self.summary()

	def summary(self):
		''' Summary stats displayed following the game. '''

		print "________________"
		print '%s turns have elapsed in this game so far.' % self.turns
		for player in self.players.values():
			print "Player: ", player.name
			print "Money: $", player.money
			property_display = [p.name for p in player.properties.values()]
			print "Monopolies: ", player.check_monopoly()
			print "Property: ", property_display
