from random import choice, shuffle
from models import Board, Bank, Cards
from config import DEFAULT_TILES, CHANCE, COMMUNITY_CHEST
from config import NON_PROPS, GAME_CARDS, UPGRADEABLE, NON_UPGRADEABLE
from db import dbInterface
from collections import namedtuple


class InvalidLogtype(Exception):
	pass

class gameLogger(object):
	''' Logs any: rent-payments, property trades,
	or significant activities for all players.'''
	def __init__(self, max_record=100):
		self.records = []
		self.valid_types = ['turn', 'rent', 'trade', 'extra']

	def log(self, msgtype=None, **kwds):
		''' Appends a new log based on game activities. Accepts argument
		'msgtype', which can be: 'turn','rent', 'trade', and 'extra'. '''
		if msgtype not in self.valid_types:
			raise InvalidLogtype("No message logged - This is not a valid message type.")
		elif msgtype == 'turn':
			msg = "%s has ended their turn." % kwds['name']
		elif msgtype == 'rent':
			msg = "%s paid %s $%s in rent." % (kwds['p1'], kwds['p2'], kwds['m'])
		elif msgtype == 'trade':
			msg = "%s --> %s - traded %s for %s." % (kwds['p1'], kwds['p2'], 
													kwds['i1'], kwds['i2'])
		print msg
		self.records.append(msg)
		return

class Bank(gameLogger):
	''' 
	The bank manages transactions, and keeps track of transactions for 
	stats purposes. It also logs transactions and trades, for display
	in-game. 
	'''

	def __init__(self, board, players):
		self.houses = 32
		self.hotels = 12
		self.balances = {}
		self.total = 0 #for stats purposes; total money
					   # from transactions handled
		self.tiles = board.prop_tiles()
		self.players = players # from engine
		self.freeparking = 100
		super(Bank, self).__init__()

	def create_accounts(self, players):
		for player in players:
			self.balances[player.name] = 0
		return 

	def disperse_transactions(self, players):
		""" Calls instance of the Bank class, and empties
		any pending transactions e.g. rent, trade-profits or taxes
		at the end of turn."""
		for player in players:
			if self.balances[player.name]:
				player.money += self.balances[player.name]
				self.total += self.balances[player.name]
				print "BANK NOTICE -- Pending adjustments of $%s have been dispersed for %s." % (self.balances[player.name], 
																			player.name)
				self.balances[player.name] = 0
			else:
				"Player %s has no outstanding balance.." % player.name
		return

	def update_rents(self):
		# if houses > 0 - set rent to h (count of houses)
		# if hotel > 0 - set rent to hotel (max of 1)
		# if mortgaged - set rent to 0
		# if len(Player.check_monopoly()) > 0 - set rent to 2x normal
		# if db.PropertyInfo(prop).type == 'rr' and count(player.properties) w/ type =='rr' > 2: rent = 25*count
		# if db.PropertyInfo(prop).type == 'utility' and count(player.properties) w/ type =='utility' > 2: rent = dice * 4 
		db = dbInterface()
		

	def props_with_houses(self, players):
		''' Find props with houses, and then change the property object's 
		'rent' attribute to new rent. '''
		db = dbInterface()
		with db.conn as conn:
			for k, v in self.tiles.items():
				if self.tiles[k]['houses'] > 0:
					print 'OKAY', k
					print 'HERE', v
					print 'OWNER', players[v['owner']].name
					print 'PROPERTIES ----', players[v['owner']].properties[k]
					#filtered = { k : self.tiles[k]} 
		return 
		

	def props_with_hotels(self):
		pass

	def utilities_rent(self):
		pass

	def railroads_rent(self):
		pass


class Player(object):

	def __init__(self, name):
		self.name = name
		self._inplay = True
		self.money = 1475
		self.properties = []
		self.position = 0
		self.others = []
		self.log = [None]
		self.board = Board(DEFAULT_TILES, None)
		self.passes = []

	def rr_rent(self):
		railroads = 4
		for prop in self.properties:
			if 'Railroad' in prop:
				railroads -= 1
		print "You pay $", (railroads * 25)

	def new_log(self, type_=''):
		print self.log[-1]
		if type_ == 'trade':
			return self.offer()
		return 

	def interact_card(self):
		Interactor.card_event(self.name, 'Chance')
		# insert interactor method here
		# insert post interact method here

	def offer(self):
		choice = raw_input("Would you like to offer (m)oney or (p)roperties? >")
		# money
		if choice.lower() == 'm':
			offer = int(raw_input('Please enter desired offer in $... '))
			return (offer, 'money')
		# property
		else:
			print "Select a choice below >"
			for n, p in enumerate(self.properties):
				print "%s) %s" % (n, p)
				choice_limit = n
			prop = int(raw_input('> '))
			return (self.properties[prop], 'property')

	def total_assets(self):
		''' Returns total financial assets of a player, represented
		as a dictionary containing the total money, houses and hotels 
		owned by a player. '''
		total_houses = 0
		total_hotels = 0
		for prop in self.properties:
			total_houses += self.board.tiles[prop]['houses']
			total_hotels += self.board.tiles[prop]['hotels']	
		return {'money': self.money ,'houses': total_houses, 
				'hotels': total_hotels}		

	def pay_rent(self, property_owner, property_, bank):
		print "You owe %s rent." % property_owner
		bank.balances[property_owner] += property_.rent
		self.money -= property_.rent
		bank.log(msgtype='rent', p1=self.name, p2=property_owner, 
			m=property_.rent)
		return 


	def build_property(self):
		''' '''
		pass

	def check_monopoly(self):
		pass

	def mortgage_property(self):
		''' '''
		pass



class TradeError(Exception):
	pass

class Interactor(object):

	players = None
	board = None
	bank = None
	cards = None
	db = None

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
		p[r].log.append(offer)
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

		cls.bank.log(msgtype='trade', p1=s, p2=r, i1=item, i2=response[0])
		return

	@classmethod
	def card_event(cls, player, current_location):
		''' '''
		db = cls.db
		p = cls.players[player]
		with db.conn as conn:
			# select a card from top of the deck
			card = cls.cards.select(current_location.lower())
			if db.card_info(conn, current_location, card):
				received_card = db.card_info(conn, current_location, card)
			# for general 'money' type cards
			if received_card.category == "money":

				# calls card_repairs - works
				assets = p.total_assets()
				if received_card.tag == "GENRP":
					print "You own %s houses, and %s hotels" % (assets['houses'], assets['hotels'])
					p.money -= (assets['houses'] * 25)
					print "You pay $%s for your houses." % (assets['houses'] * 25)
					p.money -= (assets['hotels'] * 100)
					print "You pay $%s for your hotels." % (assets['hotels'] * 25)

				# assessed for street repairs 
				elif received_card.tag == "STRRP":
					print "You own %s houses, and %s hotels" % (assets['houses'], assets['hotels'])
					p.money -= (assets['houses'] * 40)
					p.money -= (assets['hotels'] * 115)

				# you have been elected chairman of the board
				elif received_card.tag == "CHBRD":
					print "Drew card: ", card
					print "-- ", received_card.description
					for other in p.others:
						p.money -= received_card.effect
						other.money += received_card.effect

				# grand opera night  
				elif received_card.tag == "GRDON":
					print "Drew card: ", card
					print "-- ", received_card.description
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					print "Received a total of $%s for other players." % (len(p.others) * received_card.effect)

				# it is your birthday 
				elif received_card.tag == "YBDAY":
					print "Drew card: ", card
					print "-- ", received_card.description
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					print "Received a total of %s for other players." % (len(p.others) * received_card.effect)

				# normal 'Money' card											
				else:
					print "Drew card: ", card
					print "-- ", received_card.description
					p.money += received_card.effect
					print "After this card, your balance is at $", p.money

			if received_card.category == "move":
				if received_card.tag == "GOTOJ":
					print "Sorry, you've gone to Jail.."
					p.position = received_card.effect
					p.jail = True
					p.jail_duration = 3

				# Go back 3 spaces
				elif received_card.tag == "GOBTS":
					p.position += received_card.effect
					print "You've moved back to ", cls.board.layout[p.position]

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
					print "You moved to nearest railroad, %s." % cls.board.layout[p.position] 
					if cls.board.layout[p.position] in p.properties:
						print "You already own this property."
						return
					for other in p.others:
						# fix this function, so that if it's owned by someone else,
						# multiple normally entitled rent (fix this so that it scales appropriately)
						# by two
						if cls.board.layout[p.position] in other.properties:
							railroads = 1
							for prop in other.properties:
								if 'Railroad' in prop:
									railroads += 1
							print "You owe %s $%s in rent." % (other.name, (25*railroads))

				# Advance to nearest Utility
				elif received_card.tag == "ADVNU":
					if 0 <= p.position < 21:
						p.position = 12
					elif 22 <= p.position < 40:
						p.position = 28
					print "You moved to nearest utility, %s." % cls.board.layout[p.position]
					if cls.board.layout[p.position] in p.properties:
						print "You already own this property."
						return
					for other in p.others:
						if cls.board.layout[p.position] in other.properties:
							print "%s owns this already!" % other.name
							die1 = choice(range(1, 7))
							die2 = choice(range(1, 7))
							p.money -= ((die1 + die2) * 10)
							other.money += ((die1 + die2) * 10)
							print "You paid %s $%s!" % (other.name, ((die1 + die2) * 10))

				# Normal 'move' card
				else:
					print "Drew card: ", card
					print "-- ", received_card.description
					# If you pass go, collect $200
					print "if this is negative, you should pass go!", received_card.effect - p.position
					if received_card.effect - p.position < 0:
						print "You've passed Go! collect $200."
						p.money += 200
					p.position = received_card.effect
					print "YOUR CURRENT POSITION IS NOW: ", cls.board.layout[p.position]						
			if received_card.category == "item":
				p.passes.append(card)
				print "You now have a get out of jail free card! Huzzah!"


# interactor object works - CHECK
x = Player('Noah')
y = Player('Ev')
z = Player('Jack')
players = {'Noah': x, 'Ev': y, 'Jack': z}
x.properties = ['Illinois Avenue', 'Baltic Avenue', 'Park Place']
y.properties = ['Reading Railroad', 'Boardwalk', 'Electric Company', 'Vermont Avenue']
z.properties = ['New York Avenue', 'St. Charles Place', 'Water Works', 'B&O Railroad']

b = Board(DEFAULT_TILES, None)
i = Interactor()
Interactor.players = players
Interactor.board = b
Interactor.bank = Bank(b, players)
Interactor.cards = Cards(CHANCE, COMMUNITY_CHEST)
Interactor.db = dbInterface()
Interactor.cards.shuffle_cards()


x.board.tiles['Illinois Avenue']['houses'] += 2
x.board.tiles['Baltic Avenue']['hotels'] += 1
y.board.tiles['Boardwalk']['houses'] += 1
y.board.tiles['Vermont Avenue']['hotels'] += 3

db = dbInterface()
with db.conn as conn:
	db.property_info(conn, 'Short Line')
#print "INTERACTOR's Players -", Interactor.players
#print "INTERACTOR's Board -", Interactor.board
#print "INTERACTOR's Bank -", Interactor.bank
#print "INTERACTOR's Cards -", Interactor.cards

#Interactor.trade('Noah', 'Jack', 'New York Avenue')
for i in xrange(1, 17):
	Interactor.card_event('Jack', 'COMMUNITY CHEST')
	print '\n'

#y.interact_card()


# container for players CHECK
#for p in players:
	
#	interactor.players[str(p.name)] = p
# commit a trade between 'x' and 'y'
#interactor.trade('Noah', 'Ev', 'Boardwalk')

x = Player('Noah')
y = Player('Ev')
z = Player('Jack')
players = {'Noah': x, 'Ev': y, 'Jack': z}

b = Board(DEFAULT_TILES, None)
bank = Bank(b, players)
b.tiles['Oriental Avenue']['owner'] = x.name
b.tiles['Oriental Avenue']['houses'] += 3
b.tiles['Vermont Avenue']['owner'] = z.name
b.tiles['Vermont Avenue']['houses'] += 1
print bank.props_with_houses(players)



