import sys 
# work around for using virtualenv in sublime text 2
real_path = ['', '/Users/chrisli/.virtualenvs/monopoly/lib/python27.zip', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/plat-darwin', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/plat-mac', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/plat-mac/lib-scriptpackages', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/lib-tk', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/lib-old', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/lib-dynload', '/usr/local/Cellar/python/2.7.8_1/Frameworks/Python.framework/Versions/2.7/lib/python2.7', '/usr/local/Cellar/python/2.7.8_1/Frameworks/Python.framework/Versions/2.7/lib/python2.7/plat-darwin', '/usr/local/Cellar/python/2.7.8_1/Frameworks/Python.framework/Versions/2.7/lib/python2.7/lib-tk', '/usr/local/Cellar/python/2.7.8_1/Frameworks/Python.framework/Versions/2.7/lib/python2.7/plat-mac', '/usr/local/Cellar/python/2.7.8_1/Frameworks/Python.framework/Versions/2.7/lib/python2.7/plat-mac/lib-scriptpackages', '/Users/chrisli/.virtualenvs/monopoly/lib/python2.7/site-packages']
sys.path = real_path

from random import choice, shuffle
from gamelogger import gameLogger
from config import DEFAULT_TILES, CHANCE, COMMUNITY_CHEST
from config import NON_PROPS, GAME_CARDS, UPGRADEABLE, NON_UPGRADEABLE
from db import dbInterface
from collections import namedtuple, Counter


class Board(object):
	''' Implementation of board. Also carries 
	information of property ownership/assets built
	upon them.
	'''
	def __init__(self, layout_order, players):
		self.layout = [tile for row in layout_order
								for tile in row]		
		self.tiles = {str(tile): {"owner": None, "hotels": 0, "houses": 0, 'mortgaged': False} 
									for tile in self.layout}

	def prop_tiles(self):
		''' Returns only properties, for rent_update
		purposes. '''
		temp = dict(self.tiles)
		for tile in (NON_PROPS + GAME_CARDS):
			del temp[tile]
		return temp

	def check_ownership(self):
		for tile, player in self.tiles.items():
			if tile["owner"]:
				print "%s is owned by player" % (tile["owner"])				
		return
		
class Bank(object):
	''' 
	The bank manages transactions, and keeps track of transactions for 
	stats purposes. It also logs transactions and trades, for display
	in-game. 
	'''
	def __init__(self, board, players):
		self.houses = 32
		self.hotels = 12
		self.total = 0 #for stats purposes; total money
					   # from transactions handled
		self.tiles = board.prop_tiles()
		self.players = players # from engine
		self.freeparking = 100
		db = dbInterface()
		# setup ownable properties
		with db.conn as conn:
			self.rent_table = db.rent_table(conn)
			self.all_properties = { tile : db.property_info(conn, tile) for tile in self.tiles}

	def update_all_rents(self, players):
		''' Calls several helper functions, to make sure rent is updated
		following any applicable game event. '''
		self.props_with_assets(players)
		self.props_mortgaged(players)
		self.props_monopoly(players)
		self.utilities_rent(players)
		self.railroads_rent(players)
		return

	def props_with_assets(self, players):
		''' Find props with built assets, and then change the 'rent' key 
		in the rent_table dict to new rent. '''

		for tile_name, tile_obj in self.tiles.items():

			if tile_obj['owner'] != None:
				prop = players[tile_obj['owner']].properties[tile_name] # prop object
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

	def props_mortgaged(self, players):
		''' If a property is mortgaged, set rent to 0.'''
		for tile_name, tile_obj in self.tiles.items():
			if tile_obj['owner'] != None:
				if self.tiles[tile_name]['mortgaged'] == True:
					self.rent_table[tile_name]['rent'] = 0
		return

	def props_monopoly(self, players):
		''' Sets all rents to 2x, when a monopoly exists. '''
		for name, play_obj in players.items():
			monopolies = play_obj.check_monopoly()
			for prop in play_obj.properties.values():
				if prop.type in monopolies and (self.tiles[prop.name]['houses'] == 0 
										   and self.tiles[prop.name]['hotels'] == 0):
					# limits monopoly multiplier
					if self.rent_table[prop.name]['rent'] != (2 * prop.rent):
						self.rent_table[prop.name]['rent'] *= 2
		return

	def utilities_rent(self, players):
		''' If a player owns all utilities, set base rent to $10.'''

		for name, play_obj in players.items():
			util_count = 0
			for prop in play_obj.properties.values():
				if prop.type == 'utility':
					util_count += 1
			if util_count == 2:
				for prop_name, prop_info in self.rent_table.items():
					if prop_info['type'] == 'utility':
						self.rent_table[prop_name]['rent'] = 10
				return
		return

	def railroads_rent(self, players):
		''' Adjusts railroad rent to account for rent multiplier. (+$25 ea)'''

		for name, play_obj in players.items():
			rr_count = 0
			for prop in play_obj.properties.values():
				if prop.type == 'rr':
					rr_count += 1
			if rr_count == 0:
				continue
			for prop_name, prop_info in self.rent_table.items():
				rent = 25 * (2 ** (rr_count - 1))
				if prop_info['type'] == 'rr':
					self.rent_table[prop_name]['rent'] = rent
		return


class Player(object):
	''' the living and breathing entity of a Player in game

		- forfeit
	'''

	def __init__(self, name, board, cards):
		self.__inplay = True
		self.name = name
		self.board = board
		self.cards = cards
		self.passes = []
		self.properties = {}
		self.money = 1475
		self.position = 0
		self.jail = False
		self.jail_duration = 0
		self.others = []

	def current_position(self):
		return "Currently at %s" % self.board,layout[self.position]
		pass

	def roll_dice(self, board, bank, cards):
		# if in jail, use jail_interaction method
		print ' Money: $%s' % self.money
		print '-' * 15

		#print "Interactor class methods check.", Interactor.trade('Ev', 'Noah', 'Vermont Avenue')
		if self.jail == True:
			self.interact_jail()
			return self.post_interact(board, bank)
		die1 = choice(range(1, 7))
		die2 = choice(range(1, 7))
		print "You rolled: [[%s],[%s]]" % (die1, die2) 
		print "You're moving %s spaces" % (die1 + die2)
		gameLogger.add_log(msgtype='dice', name = self.name, d1= die1, d2 = die2)
		old_position = self.position

		# If you pass Go, collect $200
		if self.position + (die1 + die2) >= 40:
			print "You've passed Go: Collect $200!" 
			self.money += 200
			self.position = (self.position + (die1 + die2)) % 40
		else:	
			self.position += (die1 + die2)
		current_location = self.board.layout[self.position]
		print "You've landed on %s." % current_location

		msg = "'%s' landed on '%s'." % (self.name, current_location)
		gameLogger.add_log(msg=msg)
		return current_location

	def interact(self, current_location, board, bank, cards):
		''' Given the current position (name of tile), proceed with the appropriate interaction.
		You can liken this to a 'staging' zone for interactions. '''
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
			self.interact_nonprop(cards, board, bank, current_location)
			return

		# interact with current tile, engage in normal game behavior
		else:
			self.interact_prop(board, bank, current_location)
		return

	def interact_prop(self, board, bank, current_location):
		""" checks tile player is currently on, 
		prompts the player to decide what to do.
		"""
		
		owned = False
		if current_location in self.properties:
			print "You already own %s." % current_location
			owned = True
		if owned == False:
			property_ = bank.all_properties[current_location]
			
			# Pay rent if already owned by someone else.
			if board.tiles[property_.name]['owner']:
				self.pay_rent(board.tiles[property_.name]['owner'], property_, bank)
				return self.post_interact(board, bank)
			
			# Prompt Player to purchase property_ if unclaimed.
			self.purchase(board, property_, bank)
			return self.post_interact(board, bank)
		return self.post_interact(board, bank)


	def interact_nonprop(self, cards, board, bank, current_location):
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
			gameLogger.add_log(msg=msg) 

		if current_location == "Luxury Tax":
			print "Luxury Tax - Pay the bank $200."

			self.money -= 200
			bank.freeparking += 200
			msg = "'%s' paid Luxury Tax of $200." % self.name
			gameLogger.add_log(msg=msg) 

		if current_location == "Visiting/Jail":
			print "You visit the Jail .. you're not sure why."
			for other in self.others:
				if other.jail == True:
					msg = "'%s' ran into '%s' while visiting the Jail." % (self.name, other.name)
					break
	
		if current_location == "Go":
			msg = "'%s' collects $200 at 'Go'." % self.name 
			gameLogger.add_log(msg=msg)

		if current_location == "Free Parking":
			print "Congrats, you've won $%s" % bank.freeparking
			self.money += bank.freeparking
			bank.total += bank.freeparking
			msg = "'%s' has won $%s from Free Parking." % (self.name, bank.freeparking)
			gameLogger.add_log(msg=msg)
			bank.freeparking = 100
			
		return self.post_interact(board, bank)

	def post_interact(self, board, bank):
		''' Provides a menu of options for user to choose from at the end of turn.
		This should always be the final step of the interaction cycle. 
		'''

		unfinished = True
		while unfinished:
			if 'Get out of Jail Free' in self.passes and self.jail == True:
				get_out = raw_input("You have a 'Get out of Jail Free' card,\
								would you like to use it? (Y/n)")
				if get_out.lower() == 'y':
					self.jail = False
					print "You're out of jail!"
			print "Would you like to do anything else?"
			choice = raw_input("(1: End Turn 2: Request a trade 3: Display game logs) >")
			if choice == '1':
				gameLogger.add_log(msgtype='turn', name=self.name)
				print "_" * 20
				unfinished = False
			elif choice == '2':
				print "Who would you like to trade with?"
				for i, k in enumerate(bank.balances.keys()):
					print "%s : %s" % (i, k)
			elif choice == '3':
				gameLogger.push_public_logs()
				gameLogger.display()
			else:
				continue
		return 

	def interact_jail(self):
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
				else:
					msg = "'%s' unsuccessfully tried to get out of jail." % self.name
					gameLogger.add_log(msg=msg)
					print "Unsuccessful attempt!"
					self.jail_duration -= 1
					if self.jail_duration == 0:
						print "Hey, you're out of jail next turn!"
						self.jail = False
						self.money -= 50
					break	
		elif plea.lower() == 'n':
			payoff = raw_input("Pay $50 to get out? Y/n >")
			if payoff.lower() == 'y':
				msg = "'%s' paid $50 to get out of jail." % self.name
				gameLogger.add_log(msg=msg)
				self.money -= 50
				self.jail = False
		return
 
	def purchase(self, board, property_, bank):
		''' Purchase property in argument, sets up
		pending transaction for Bank to process at end of turn.'''
		print "%s costs $%s, would you like to purchase it?" % (property_.name, property_.cost)
		choice = raw_input("y/n >") # make this into a form button on Flask?
		
		if choice.lower() == 'n':
			return	
		self.money -= property_.cost
		self.properties[property_.name] = property_
		board.tiles[property_.name]['owner'] = self.name

		gameLogger.add_log(msgtype='purchase', name = self.name, 
				   property = property_.name, cost = property_.cost)
		return

	def pay_rent(self, property_owner, property_, bank):
		print "You owe %s rent." % property_owner
		if bank.players[property_owner] in self.others:
			recipient = bank.players[property_owner] 
		else:
			return
		recipient.money += bank.rent_table[property_.name]['rent']
		self.money -= bank.rent_table[property_.name]['rent']
		gameLogger.add_log(msgtype='rent', p1=self.name, p2=property_owner, 
			m=property_.rent)
		return 

	def total_assets(self):
		''' Returns total financial assets of a player, represented
		as a dictionary containing the total money, houses and hotels 
		owned by a player. '''
		total_houses = 0
		total_hotels = 0
		for prop in self.properties.values():
			total_houses += self.board.tiles[prop.name]['houses']
			total_hotels += self.board.tiles[prop.name]['hotels']	
		return {'money': self.money ,'houses': total_houses, 
				'hotels': total_hotels}

	def check_monopoly(self):
		db = dbInterface()
		colors = [p.type for p in self.properties.values()]
		c = Counter(colors)
		with db.conn as conn:
			monopolies = [color for color, count in c.items() 
						if count == db.prop_set_length(conn, color)[0]]
		#print "You may build assets for these property types: ", monopolies
		return monopolies


	def build_asset(self, number, property_, bank):
		''' You start by building a house, and then automatically
		transition to hotel. There's a limit of 1 hotel in this
		game. To be activated in post-interaction'''
		# if hotel already here, don't build.
		if self.board.tiles[property_.name]['hotels'] == 1:
			return " -- You can't build anymore properties here!"
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
				print "Built 1 hotel at %s, it cost $%s." % (property_.name, (old_money - self.money))
			else:
				self.board.tiles[property_.name]['houses'] += number	
				bank.houses -= number
				print "Built %s house at %s, it cost $%s." % (number, property_.name, (old_money - self.money))	
		else:
			print "Sorry, you don't seem to have a monopoly for this set of properties."
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
		print ' -- %s sold %s houses for $%s.' % (self.name, number, (self.money - old_money))	
		return


	def mortgage_property(self, property_, bank):
		''' To be activated in post-interaction. This is a switch for mortgaging properties.
		If you decide to mortgage property, you're also agreeing to sell off all of its built 
		assets. '''
		
		if self.board.tiles[property_.name]['mortgaged'] == True:
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
		
	def __str__(self):
		return "Your name is %s." % self.name


class Cards(object):
	''' 
	A representation of both decks of game cards. Used by game engine to 
	manage card circulation, and interpretation of each card's effects.
	'''
	def __init__(self, chance, communitychest):
		self.chance = CHANCE
		self.communitychest = COMMUNITY_CHEST

	def shuffle_cards(self):
		shuffle(self.chance)
		shuffle(self.communitychest)
		return

	def select(self, card_type):
		''' taking from the top of a card pile'''
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

class TradeError(Exception):
	pass

class Interactor(object):

	players = None
	board = None
	bank = None
	cards = None

	def __init__(self):
		pass

	@classmethod
	def trade(cls, s, r, item):
		''' Edit to test trade box mechanics.
		Make sure to include code that transitions
		ownership of the property between players
		'''

		p = cls.players
		transaction_type = ['p', None]
		if (s or r) not in p.keys():
			raise TradeError('Either the sender or recipient is not in this game.')
		offer = "%s would like to trade '%s'. What would you like to offer? >" % (s, item)
		gameLogger[r].add_log(offer)
		response = p[r].new_log(type_='trade')
		if response[1] == 'money':
			summary = "%s is willing to trade '$%s' for your '%s'. Is this okay? >" % (r, response[0], item)
			transaction_type[1] = 'm'
		else:
			summary = "%s is willing to trade '%s' for your '%s'. Is this okay? >" % (r, response[0], item)
			transaction_type[1] = 'p'
		deal = raw_input(summary)
		if deal.lower() == 'y':
			if transaction_type[1] == 'm':
				p[s].money += response[0]
				p[r].money -= response[0]
				p[s].properties.remove(item) 
				p[r].properties.append(item)
			else:
				p[s].properties.append(response[0])
				p[r].properties.remove(response[0])
				p[s].properties.remove(item)
				p[r].properties.append(item)
				pass

		print '%s has $%s money left.' % (cls.players[r].name, cls.players[r].money)
		print cls.players[s].properties
		print cls.players[r].properties

		gameLogger.add_log(msgtype='trade', p1=s, p2=r, i1=item, i2=response[0])
		return

	@classmethod
	def card_event(cls, player, current_location):
		''' '''
		db = dbInterface()
		p = cls.players[player]
		with db.conn as conn:
			# select a card from top of the deck
			card = cls.cards.select(current_location.lower())
			if db.card_info(conn, current_location, card):
				received_card = db.card_info(conn, current_location, card)
			print "Drew card: ", card
			print "-- ", received_card.description
			gameLogger.add_log(msgtype='card event', name=p.name, card=card, 
				desc=received_card.description)
			# for general 'money' type cards
			if received_card.category == "money":

				# calls card_repairs - works
				assets = p.total_assets()
				if received_card.tag == "GENRP":
					print "You own %s houses, and %s hotels" % (assets['houses'], assets['hotels'])
					p.money -= (assets['houses'] * 25)
					p.money -= (assets['hotels'] * 100)
					msg = "'%s' paid $%s and $%s for repairs to houses and hotels, respectively." % (p.name, 
													 assets['houses'] * 25, assets['hotels'] * 100)
					gameLogger.add_log(msg=msg)

				# assessed for street repairs 
				elif received_card.tag == "STRRP":
					print "You own %s houses, and %s hotels" % (assets['houses'], assets['hotels'])
					p.money -= (assets['houses'] * 40)
					p.money -= (assets['hotels'] * 115)
					msg = "'%s' paid $%s and $%s for repairs to houses and hotels, respectively." % (p.name, 
													 assets['houses'] * 25, assets['hotels'] * 100)
					gameLogger.add_log(msg=msg)

				# you have been elected chairman of the board
				elif received_card.tag == "CHBRD":
					for other in p.others:
						p.money -= received_card.effect
						other.money += received_card.effect
					msg = "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
					gameLogger.add_log(msg=msg)

				# grand opera night  
				elif received_card.tag == "GRDON":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					msg =  "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
					gameLogger.add_log(msg=msg)

				# it is your birthday 
				elif received_card.tag == "YBDAY":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					msg =  "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
					gameLogger.add_log(msg=msg)

				# normal 'Money' card											
				else:
					p.money += received_card.effect
					msg = "'%s' gained $%s." % (p.name, received_card.effect)
					gameLogger.add_log(msg=msg)

				return p.post_interact(cls.board, cls.bank)
			if received_card.category == "move":

				# Go to jail
				if received_card.tag == "GOTOJ":
					p.position = received_card.effect
					p.jail = True
					p.jail_duration = 3
					msg = "'%s' went to '%s'." % (p.name, 'Jail')
					gameLogger.add_log(msg=msg)
					p.post_interact(cls.board, cls.bank)

				# Go back 3 spaces
				elif received_card.tag == "GOBTS":
					p.position += received_card.effect
					print "You've now on ...", cls.board.layout[p.position]
					current_location = cls.board.layout[p.position]
					msg = "'%s' moved back 3 spaces to '%s'." % (p.name, current_location)
					gameLogger.add_log(msg=msg)
					p.interact(current_location, cls.board, cls.bank, p.position)
					
				# Advance to nearest Railroad
				elif received_card.tag == "ADVNR":
					if 0 <= p.position < 10:
						p.position = 5
					elif 10 < p.position < 20:
						p.position = 15
					elif 20 < p.position < 30:
						p.position = 25
					elif 30 < p.position < 40: 
						p.position = 35
					current_location = cls.board.layout[p.position] 
					print "You moved to nearest railroad, %s." % current_location
					msg = "'%s' moved to nearest railroad, '%s'." % (p.name, current_location)
					gameLogger.add_log(msg=msg)
				
					if current_location in p.properties:
						print "You already own this property."
						return

					for other in p.others:
						if current_location in other.properties:
							rent = bank.rent_table[p.position]['rent'] * 2
							p.money -= rent
							other.money += rent
							print "You owe %s $%s in rent." % (other.name, rent)
							gameLogger.add_log(msgtype=rent, p1=p.name, 
												p2=other.name, m=rent)
							return

					p.purchase(cls.board, cls.bank.all_properties[current_location], cls.bank)
					p.post_interact(cls.board, cls.bank)
					return

				# Advance to nearest Utility
				elif received_card.tag == "ADVNU":
					if 0 <= p.position < 21:
						p.position = 12
					elif 22 <= p.position < 40:
						p.position = 28
					current_location = cls.board.layout[p.position]	
					print "You moved to nearest utility, %s." % current_location
					msg = "'%s' moved to nearest utility, '%s'." % (p.name, current_location)
					gameLogger.add_log(msg=msg)

					if current_location in p.properties:
						print "You already own this property."
						return

					for other in p.others:
						if current_location in other.properties:
							die1 = choice(range(1, 7))
							die2 = choice(range(1, 7))
							p.money -= ((die1 + die2) * 10)
							other.money += ((die1 + die2) * 10)
							print "You paid %s $%s!" % (other.name, ((die1 + die2) * 10))
							gameLogger.add_log(msgtype=rent, p1=p.name, 
												p2=other.name, m=((die1 + die2) * 10))
						
					p.purchase(cls.board, cls.bank.all_properties[current_location], cls.bank)
					p.post_interact(cls.board, cls.bank)
					return	

				# Normal 'move' card
				else:
					if received_card.effect - p.position < 0:
						print "You've passed Go! collect $200."
						p.money += 200
					p.position = received_card.effect
					current_location = cls.board.layout[p.position]
					p.interact(current_location, cls.board, cls.bank, p.position)

			if received_card.category == "item":
				p.passes.append(card)
				msg = "'%s' received a 'Get Out of Jail Free' card!" % p.name
				gameLogger.add_log(msg=msg)
				p.post_interact(cls.board, cls.bank)

if __name__ == '__main__':
	b = Board(DEFAULT_TILES, None)
	c = Cards(COMMUNITY_CHEST, CHANCE)

	x = Player('Noah', b, c)
	y = Player('Ev', b, c)
	z = Player('Jack', b, c)
	players = {'Noah': x, 'Ev': y, 'Jack': z}
	bank = Bank(b, players)
	Interactor.players = players
	Interactor.board = b
	Interactor.bank = bank
	Interactor.cards = c
	Interactor.db = dbInterface()



