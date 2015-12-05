''' Game Models.
Includes all essential in-game models; Board, Bank, Player and Cards
'''

from random import choice, shuffle
from gamelogger import GameLogger, ansi_tile
from interactor import Interactor
from config import CHANCE, COMMUNITY_CHEST
from config import NON_PROPS, GAME_CARDS
from db import DbInterface
from collections import Counter


class Board(object):
	''' Implementation of Monopoly board. Instantiated as argument for
		class Monopoly().

		:layout_order: - Takes a 4 x 10 matrix (4 lists within one list) of
		property names in correct layout, and uses that to set the board.
		:players: -  Dictionary of players, set as attribute in Monopoly.setup()
	'''

	def __init__(self, layout_order):
		self.layout = [tile for row in layout_order for tile in row]
		self.tiles = {str(tile): {"owner": None, "hotels": 0,
					 			 "houses": 0, 'mortgaged': False}
					 			 for tile in self.layout}

	def prop_tiles(self):
		''' Returns only properties, for rent_update
		purposes. '''

		temp = dict(self.tiles)
		for tile in (NON_PROPS + GAME_CARDS):
			del temp[tile]
		return temp

	def check_ownership(self, property_name):
		''' Scan all properties for ownership. '''

		return self.prop_tiles()[property_name]["owner"]


class Bank(object):
	''' The bank manages transactions, and keeps track of transactions for
	stats purposes. It also logs transactions and trades, for display
	in-game.

	:board: - instance of Board() object, instantiated in Monopoly()
	:players: - Dictionary of players, set as attribute in Monopoly.setup()
	'''

	def __init__(self, board, players):
		self.houses = 32
		self.hotels = 12
		self.tiles = board.prop_tiles()
		self.players = players  # from engine
		self.freeparking = 100
		db = DbInterface()
		# setup ownable properties
		with db.conn as conn:
			self.rent_table = db.rent_table(conn)
			self.all_properties = {tile: db.property_info(conn, tile)
			                      for tile in self.tiles}

	def update_all_rents(self, players):
		''' Calls several helper functions, to make sure rent is updated
		following any applicable game event. '''

		self.props_with_assets(players)
		self.props_mortgaged()
		self.props_monopoly(players)
		self.utilities_rent(players)
		self.railroads_rent(players)
		return

	def props_with_assets(self, players):
		''' Find props with built assets, and then change the 'rent' key
		in the rent_table dict to new rent. '''

		for tile_name, tile_obj in self.tiles.items():
			prop_type = self.rent_table[tile_name]['type']

			if prop_type == 'rr' or prop_type == 'utility':
				continue
			if tile_obj['owner'] is not None:
				prop = players[tile_obj['owner']].properties[tile_name]  # prop object

			if self.tiles[tile_name]['houses'] == 1:
				self.rent_table[tile_name]['rent'] = prop.h1

			elif self.tiles[tile_name]['houses'] == 2:
				self.rent_table[tile_name]['rent'] = prop.h2

			elif self.tiles[tile_name]['houses'] == 3:
				self.rent_table[tile_name]['rent'] = prop.h3

			elif self.tiles[tile_name]['houses'] == 4:
				self.rent_table[tile_name]['rent'] = prop.h4

			elif self.tiles[tile_name]['hotels'] > 0:
				self.rent_table[tile_name]['rent'] = prop.hotel
		return

	def props_mortgaged(self):
		''' If a property is mortgaged, set rent to 0.'''

		for tile_name, tile_obj in self.tiles.items():
			if tile_obj['owner'] is not None:
				if self.tiles[tile_name]['mortgaged'] is True:
					self.rent_table[tile_name]['rent'] = 0
		return

	def props_monopoly(self, players):
		''' Sets all rents to 2x, when a monopoly exists. '''

		for player in players.values():
			monopolies = player.check_monopoly()
			for prop in player.properties.values():
				if prop.type in monopolies and (self.tiles[prop.name]['houses'] == 0
							and self.tiles[prop.name]['hotels'] == 0):
					# limits monopoly multiplier
					if self.rent_table[prop.name]['rent'] != (2 * prop.rent):
						self.rent_table[prop.name]['rent'] *= 2
		return

	def utilities_rent(self, players):
		''' If a player owns all utilities, set base rent to $10.'''

		ec_owner = self.tiles['Electric Company']['owner']
		ww_owner = self.tiles['Water Works']['owner']

		if ec_owner == ww_owner:
			self.rent_table['Electric Company']['rent'] = 10
			self.rent_table['Water Works']['rent'] = 10

		else:
			self.rent_table['Electric Company']['rent'] = 4
			self.rent_table['Water Works']['rent'] = 4

		return

	def railroads_rent(self, players):
		''' Adjusts railroad rent to account for rent multiplier (+$25 ea) '''


		for player in players.values():
			owner = player.name
			rr_count = 0
			for prop in player.properties.values():
				if prop.type == 'rr':
					rr_count += 1
			if rr_count == 0:
				continue
			for prop_name, prop_info in self.rent_table.items():		
				if prop_info['type'] == 'rr' and self.tiles[prop_name]['owner'] == player.name:
					rent = lambda rr_count : 25 * (2 ** (rr_count - 1))
					self.rent_table[prop_name]['rent'] = rent(rr_count)
		return


class Player(object):
	''' Embodies all states and behaviors of a player, interacting
	with nearly all other game models.

	A player enters the following 'interaction chain':

	Player.roll_dice() --> Player.interact() -->
	Player.<...specific interaction method...> --> Player.post_interact()

	:name: - name of player
	:board: - instance of Board() object, instantiated in Monopoly()
	:cards: - instance of Cards() object, instantiated in Monopoly()
	'''

	def __init__(self, name, board, cards):
		self._inplay = True
		self.name = name
		self.board = board
		self.cards = cards
		self.passes = []
		self.properties = {}
		self.money = 1475
		self.position = 0
		self.last_roll = 0
		self.jail = False
		self.jail_duration = 0
		self.repeat_turn = False
		self.repeat_count = 0
		self.others = []

	def current_position(self):
		''' Returns name of current tile Player is standing on. '''
		return self.board.layout[self.position]

	def roll_dice(self, board, bank):
		''' First stage of the interaction chain.
		Check if in jail --> Roll dice --> Move to new position	'''

		# send to jail if this is the third double
		if self.repeat_count >= 3:
			self.jail = True
			self.duration = 3

		# if in jail, use jail_interaction method
		if self.jail is True:
			self.interact_jail()
			return self.post_interact(board, bank)
		die1 = choice(range(1, 7))
		die2 = choice(range(1, 7))
		print "You rolled: [[%s],[%s]]" % (die1, die2)
		print "You're moving %s spaces" % (die1 + die2)
		GameLogger.add_log(msgtype='dice', name=self.name, d1=die1, d2=die2)

		# repeat turn
		if die1 == die2:
			self.repeat_count += 1
			self.repeat_turn = True

		# If you pass Go, collect $200
		if self.position + (die1 + die2) >= 40:
			print "You've passed Go: Collect $200!"
			self.money += 200
			self.position = (self.position + (die1 + die2)) % 40
		else:
			self.position += (die1 + die2)

		self.last_roll = die1 + die2
		current_location = self.board.layout[self.position]
		cl_display = ansi_tile(current_location)
		print "You've landed on %s." % cl_display

		msg = "'%s' landed on '%s'." % (self.name, cl_display)
		GameLogger.add_log(msg=msg)
		return current_location

	def interact(self, current_location, board, bank):
		''' Given the current position (name of tile), proceed with
		the appropriate interaction. You can liken this to a
		'staging' zone for interactions. '''

		# interact w/ GAME_CARDS
		if current_location in GAME_CARDS:
			if current_location == 'Chance':
				Interactor.card_event(self.name, 'Chance')
				return
			elif current_location == 'Community Chest':
				Interactor.card_event(self.name, 'Community Chest')
				return

		# interact w/ tiles that are neither GAME_CARDS nor properties
		if current_location in NON_PROPS:
			self.interact_nonprop(board, bank, current_location)
			return

		# interact with current tile, engage in normal game behavior
		else:
			self.interact_prop(board, bank, current_location)
		return

	def interact_prop(self, board, bank, current_location):
		''' Checks tile player is currently on,
		prompts the player to decide what to do. '''

		owned = False
		if current_location in self.properties:
			print "You already own %s." % current_location
			owned = True
		if owned is False:
			property_ = bank.all_properties[current_location]
			# Pay rent if already owned by someone else.
			if board.tiles[property_.name]['owner']:
				self.pay_rent(board.tiles[property_.name]['owner'], property_, bank)
				return self.post_interact(board, bank)
			# Prompt Player to purchase property_ if unclaimed.
			self.purchase(board, property_)
			return self.post_interact(board, bank)
		return self.post_interact(board, bank)

	def interact_nonprop(self, board, bank, current_location):
		''' Guides interactions for tiles that are not properties or
		card events. '''

		if current_location == "Go to Jail":
			self.jail = True
			self.position = 10
			self.jail_duration = 3

		if current_location == "Income Tax":
			print "Income Tax - Pay the bank $100."
			self.money -= 100
			bank.freeparking += 100
			msg = "'%s' paid Income Tax of $100." % self.name
			GameLogger.add_log(msg=msg)

		if current_location == "Luxury Tax":
			print "Luxury Tax - Pay the bank $200."

			self.money -= 200
			bank.freeparking += 200
			msg = "'%s' paid Luxury Tax of $200." % self.name
			GameLogger.add_log(msg=msg)

		if current_location == "Visiting/Jail":
			print "You visit the Jail .. you're not sure why."
			for other in self.others:
				if other.jail is True:
					msg = "'%s' ran into '%s' while visiting the Jail." % (self.name, other.name)
					break

		if current_location == "Go":
			msg = "'%s' collects $200 at 'Go'." % self.name
			GameLogger.add_log(msg=msg)

		if current_location == "Free Parking":
			print "Congrats, you've won $%s" % bank.freeparking
			self.money += bank.freeparking
			msg = "'%s' has won $%s from Free Parking." % (self.name, bank.freeparking)
			GameLogger.add_log(msg=msg)
			bank.freeparking = 100
		return self.post_interact(board, bank)

	def interact_jail(self):
		''' The interaction stage if a player is in jail.

		Involves attempting to roll three snake-eyes to get out, or
		prompting the player to pay $50. '''

		plea = raw_input("Try rolling three snake-eyes to get out? Y/n >")
		if plea.lower() == 'y':
			snake_eye_trials = 3
			print "Attempting to roll 3 doubles..."
			while snake_eye_trials > 0:
				die1 = choice(range(1, 7))
				die2 = choice(range(1, 7))
				print die1, die2
				if die1 == die2:
					snake_eye_trials -= 1
					if snake_eye_trials == 0:
						print "You rolled out of jail!"
						self.jail = False
						break
				else:
					msg = "'%s' unsuccessfully tried to get out of jail." % self.name
					GameLogger.add_log(msg=msg)
					print "Unsuccessful attempt!"
					self.jail_duration -= 1
					if self.jail_duration <= 0:
						print "Hey, you're out of jail next turn!"
						self.jail = False
						self.money -= 50
					return

		elif plea.lower() != 'y':
			payoff = raw_input("Pay $50 to get out? Y/n >")
			if payoff.lower() == 'y':
				msg = "'%s' paid $50 to get out of jail." % self.name
				GameLogger.add_log(msg=msg)
				self.money -= 50
				self.jail = False
		return

	def post_interact(self, board, bank):
		''' Provides a menu of options for user to choose from at the end of turn.
		This should always be the final step of the interaction cycle. '''

		unfinished = True
		while unfinished:
			options = ['End Turn', 'Trade', 'Mortgage Property',
						'Purchase Asset', 'Sell Asset', 'Inspect Self',
						'Others Inspect', 'Display Game Logs']

			# add additional options based on state
			if len(self.check_monopoly()) == 0:
				options.remove('Purchase Asset')

			for tile_name in self.properties:
				if (board.tiles[tile_name]['hotels'] == 0 and board.tiles[tile_name]['houses'] == 0):
					options.remove('Sell Asset')
					break

			if not self.properties:
				options.remove('Mortgage Property')

			# use Get out of Jail Free if it's available
			if 'Get out of Jail Free' in self.passes and self.jail is True:
				get_out = raw_input("You have a 'Get out of Jail Free' card, would you like to use it? (Y/n)")
				if get_out.lower() == 'y':
					self.jail = False
					print "You're out of jail!"

			# options menu
			print "Would you like to do anything else?"
			menu = {}
			for menu_item in options:
				print "'%s' : %s." % (menu_item[0].lower(), menu_item)

			menu_choice = raw_input("Enter your choice here >> ").lower()
			if menu_choice == 'e':
				GameLogger.add_log(msgtype='turn', name=self.name)
				print "_" * 40
				print '\n'
				unfinished = False				# End Turn

			elif menu_choice == 't':
				self.trade_prompt(bank)			# Trade

			elif menu_choice == 'm':
				pass							# Mortgage Property

			elif menu_choice == 'p':
				self.build_asset_prompt(bank)   # Purchase Asset

			elif menu_choice == 'i':
				self.inspect_self()				# Inspect Self

			elif menu_choice == 'o':
				self.inspect_others()			# Inspect Others

			elif menu_choice == 'd':
				GameLogger.push_public_logs()   # Display Game Logs
				GameLogger.display()

			elif menu_choice == 'rt':
				for i in bank.rent_table.items():
					print i
			else:
				continue

		# If you roll doubles - go again
		if self.repeat_turn is True:
			msg = "It's %s's turn again, because doubles were rolled!" % self.name
			print "It's your turn, again %s!" % self.name
			GameLogger.add_log(msg=msg)
			self.repeat_turn = False
			current_location = self.roll_dice(board, bank)
			if current_location is not None:
				self.interact(current_location, board, bank)
		self.repeat_count = 0
		return

	def purchase(self, board, property_):
		''' Purchase property in argument, sets up
		pending transaction for Bank to process at end of turn. '''

		if self.money - property_.cost < 0:
			print "You don't have enough money to make this purchase."
			return
		ongoing = True

		while ongoing:
			print "%s costs $%s, would you like to purchase it?" % (property_.name,
																	property_.cost)
			purchase_choice = raw_input("(y/n) >").lower()
			if purchase_choice != 'y' and purchase_choice != 'n':
				continue
			elif purchase_choice.lower() == 'n':
				return

			self.money -= property_.cost
			self.properties[property_.name] = property_
			board.tiles[property_.name]['owner'] = self.name
			ongoing = False

		GameLogger.add_log(msgtype='purchase', name=self.name,
							property=property_.name, cost=property_.cost)
		return

	def pay_rent(self, property_owner, property_, bank):
		''' Based on up-to-date rent information from Bank.rent_table,
		the Player pays the property_owner the appropriate rent for landing
		on their property. '''

		print "You owe %s rent." % property_owner

		if bank.players[property_owner] in self.others:
			recipient = bank.players[property_owner]
		else:
			return

		rent = bank.rent_table[property_.name]['rent']

		if property_.type == 'utility':
			rent *= self.last_roll

		recipient.money += rent
		self.money -= bank.rent_table[property_.name]['rent']
		GameLogger.add_log(msgtype='rent', p1=self.name,
							p2=property_owner, m=rent)
		return

	def check_monopoly(self):
		''' Checks the color groups of a Player's properties, returning
		a list of 'colors' that the Player has monopolies to. '''

		db = DbInterface()
		colors = [p.type for p in self.properties.values()]
		c = Counter(colors)
		with db.conn as conn:
			monopolies = [color for color, count in c.items()
							if count == db.prop_set_length(conn, color)[0]]
		return monopolies

	def total_assets(self):
		''' Returns total financial assets of a player, represented
		as a dictionary containing the total money, houses and hotels
		owned by a player. '''

		total_houses = 0
		total_hotels = 0
		for prop in self.properties.values():
			total_houses += self.board.tiles[prop.name]['houses']
			total_hotels += self.board.tiles[prop.name]['hotels']
		return {'money': self.money, 'houses': total_houses,
				'hotels': total_hotels}

	def build_asset_prompt(self, bank):
		''' User interface that prompts user to select property they
		want to build on. '''

		menu = {}
		monopolies = self.check_monopoly()
		num = -1
		for num, prop in enumerate(self.properties.values()):
			num += 1
			if prop.type in monopolies:
				print "%s : %s" % (str(num), prop.name)
				menu[num] = self.properties[prop.name]
		print "%s : %s" % (str(num + 1), 'Cancel')
		menu[str(num + 1)] = 'Cancel'
		ongoing = True
		while ongoing:

			print "What property would you like to build on?"
			prop_choice = raw_input(" >> ")
			if prop_choice not in menu.keys():
				continue
			elif prop_choice == str(num + 1):
				ongoing = False
				return

			number_to_build = int(raw_input("How much do you want to build? (Max is 5 - a hotel.) "))
			print "So you want to build %s structures on %s?" % (number_to_build, menu[prop_choice].name)

			confirm = raw_input("(y/n) >> ")
			if confirm.lower() == 'y':
				self.build_asset(number_to_build, menu[prop_choice], bank)
				ongoing = False
			else:
				continue
		return

	def build_asset(self, number, property_, bank):
		''' You start by building a house, and then automatically
		transition to hotel. There's a limit of 1 hotel in this
		game. To be activated in post-interaction. '''

		# if hotel already here, don't build.
		if self.board.tiles[property_.name]['hotels'] >= 1:
			print " -- You can't build anymore properties here!"
			return
		# if the # of houses we want to build > the amount we can build
		# build a hotel
		current_developments = self.board.tiles[property_.name]['houses']
		if (number + current_developments) > 5:
			bank.houses += self.board.tiles[property_.name]['houses']
			self.board.tiles[property_.name]['houses'] *= 0
		old_money = self.money
		# check if a monopoly exists to begin with
		if property_.type in self.check_monopoly():
			# Build houses, and then hotels
			if property_.type in ['purple', 'periwinkle']:
				u_cost = 50
				self.money -= u_cost * number
			elif property_.type in ['magenta', 'orange']:
				u_cost = 100
				self.money -= u_cost * number
			elif property_.type in ['red', 'yellow']:
				u_cost = 150
				self.money -= u_cost * number
			elif property_.type in ['green', 'blue']:
				u_cost = 200
				self.money -= u_cost * number
			if (number + current_developments) >= 5:
				self.board.tiles[property_.name]['hotels'] += 1
				bank.hotels -= 1
				self.money += ((number + current_developments) - 5) * u_cost
				print "Built 1 hotel at %s, it cost $%s." % (property_.name,
															(old_money - self.money))
				msg = "'%s' built 1 hotel at %s." % (self.name,
													ansi_tile(property_.name))
			else:
				self.board.tiles[property_.name]['houses'] += number
				bank.houses -= number
				print "Built %s house at %s, it cost $%s." % (number,
									property_.name, (old_money - self.money))
				msg = "^^ '%s' built %s houses at '%s'." % (self.name, number,
									ansi_tile(property_.name))
		else:
			print "Sorry, you don't seem to have a monopoly for this set of properties."
			return
		GameLogger.add_log(msg=msg)
		return

	def trade_prompt(self, bank):
		''' Stages the Interactor.trade function, by prompting
		the user to select who they want to trade with. '''

		menu = {}
		valid = False
		print "Who would you like to trade with?"
		for num, other in enumerate(self.others):
			print "%s : %s" % (num, other.name)
			menu[str(num)] = other
		while not valid:
			choice = raw_input(" >> ")
			if choice not in menu.keys():
				continue
			else:
				s = bank.players[self.name]  # sender
				r = menu[choice] 			 # recipient
				valid = True
		Interactor.trade(s, r)
		return

	def sell_asset(self, number, property_, bank):
		''' Sell a specified number of some type of asset for half
		of the purchase price. '''

		# if hotel already here, don't build.
		if self.board.tiles[property_.name]['owner'] != self.name:
			return 'This property and its assets are not yours to sell!'
		if number > self.board.tiles[property_.name]['houses']:
			number = self.board.tiles[property_.name]['houses']
		old_money = self.money

		# for hotels
		if self.board.tiles[property_.name]['hotels'] > 0:
			self.board.tiles[property_.name]['hotels'] *= 0
			number = 5

		# gain half value per asset
		if property_.type in ['purple', 'periwinkle']:
			self.money += (25 * number)
		elif property_.type in ['magenta', 'orange']:
			self.money += (50 * number)
		elif property_.type in ['red', 'yellow']:
			self.money += (75 * number)
		elif property_.type in ['green', 'blue']:
			self.money += (100 * number)

		if number > 4:
			self.board.tiles[property_.name]['houses'] *= number
		else:
			self.board.tiles[property_.name]['houses'] -= number
		print ' -- %s sold %s houses for $%s.' % (self.name, number,
												(self.money - old_money))
		return

	def mortgage_property(self, property_, bank):
		''' To be activated in post-interaction. This is a switch for mortgaging properties.
		If you decide to mortgage property, you're also agreeing to sell off all of its built
		assets. '''

		if self.board.tiles[property_.name]['mortgaged'] is True:
			bank.rent_table[property_.name]['rent'] = property_.rent
			self.board.tiles[property_.name]['mortgaged'] = False
			self.money -= property_.mortgage
			print "Paid $%s to regain mortgaged property, '%s'" % (property_.mortgage, property_.name)
		else:
			self.sell_asset(5, property_, bank)
			self.board.tiles[property_.name]['mortgaged'] = True
			self.money += property_.mortgage
			print "Gained $%s from mortgaged property, '%s'" % (property_.mortgage, property_.name)
		return

	def inspect_self(self):
		''' Pretty prints information regarding Player, including:

		- Current Position
		- Money
		- Properties
		- Monopolies '''

		print "_" * 40
		print " " * 20 + self.name + " " * 20 + "\n"
		print "Current Position: %s" % self.current_position()
		print "Money: \t ... $%s" % self.money
		print "Properties:"
		for prop in self.properties.values():
			print "\t ...", ansi_tile(prop.name)
		print "Monopolies:"
		for color in self.check_monopoly():
			print "\t ...", color.title()
		print "_" * 40
		return

	def inspect_others(self):
		''' Pretty prints information regarding other Players. '''

		for other in self.others:
			print "_" * 40
			print " " * 20 + other.name + " " * 20 + "\n"
			print "Current Position: %s" % other.current_position()
			print "Properties:"
			for prop in other.properties.values():
				print "\t ...", ansi_tile(prop.name)
			print "Monopolies:"
			for color in other.check_monopoly():
				print "\t ...", color.title()
			print "_" * 40
		return

	def net_worth(self):
		''' Calculates net worth of player, by returning the sum
		of a player's money, total value of assets (houses/hotels)
		and total value of properties. '''

		# asset
		assets = 0
		# properties
		properties = 0
		for property_ in self.properties.values():
			properties += property_.mortgage
			number = self.board.tiles[property_.name]['houses']
			if self.board.tiles[property_.name]['hotels']:
				number = 5
			if property_.type in ['purple', 'periwinkle']:
				assets += (25 * number)
			elif property_.type in ['magenta', 'orange']:
				assets += (50 * number)
			elif property_.type in ['red', 'yellow']:
				assets += (75 * number)
			elif property_.type in ['green', 'blue']:
				assets += (100 * number)
		total_net_worth = self.money + assets + properties
		cash_to_nw = round(self.money / float(total_net_worth), 3)
		assets_to_nw = round(assets + properties / float(total_net_worth), 3)
		return total_net_worth, cash_to_nw, assets_to_nw

	def __repr__(self):
		return "<class Player '%s'>" % self.name


class Cards(object):
	''' A representation of both decks of game cards. Used by game engine to
	manage card circulation, and interpretation of each card's effects. '''

	def __init__(self):
		self.chance = CHANCE
		self.communitychest = COMMUNITY_CHEST

	def shuffle_cards(self):
		''' Randomizes order of cards. '''
		shuffle(self.chance)
		shuffle(self.communitychest)
		return

	def select(self, card_type):
		''' Select a card from the top of the deck. '''
		if card_type == "chance":
			draw = self.chance[0]
			self.chance.remove(draw)
			self.chance.append(draw)
			return draw
		elif card_type == "community chest":
			draw = self.communitychest[0]
			self.communitychest.remove(draw)
			self.communitychest.append(draw)
			return draw
		return

if __name__ == '__main__':
	pass
	'''
	b = Board(DEFAULT_TILES, None)
	c = Cards(COMMUNITY_CHEST, CHANCE)
	db = DbInterface()

	x = Player('Noah', b, c)
	y = Player('Ev', b, c)
	z = Player('Jack', b, c)
	players = {x.name: x, y.name : y, z.name : z}
	bank = Bank(b, players)
	Interactor.players = players
	Interactor.board = b
	Interactor.bank = bank
	Interactor.cards = c
	Interactor.db = DbInterface()
	with db.conn as conn:
		x.purchase(b, db.property_info(conn, 'Mediterranean Avenue'))
		x.purchase(b, db.property_info(conn, 'Baltic Avenue'))
		y.purchase(b, db.property_info(conn, 'Ventnor Avenue'))
		y.purchase(b, db.property_info(conn, 'Atlantic Avenue'))

	#Interactor.trade(x.name, y.name, 'Mediterranean Avenue')
	#x.post_interact(b, bank)

	x.others = [other for other in bank.players.values() if other != x]
	x.trade_prompt(bank)
	'''
