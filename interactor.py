''' The Interactor class '''

from db import DbInterface
from gamelogger import GameLogger, ansi_tile_display
from random import choice


class Interactor(object):
	''' An 'interface' class, that facilitates transfer of objects
	between different game entities, such as Player, Bank or Cards,
	as well as transitions in states.'''
	players = None
	board = None
	bank = None
	cards = None

	def __init__(self):
		pass

	@classmethod
	def trade(cls, s, r):

		# load items into trade box - sender
		sender_trade_box = cls.trade_box(s)

		# load items into trade box - receiver
		print "Sending offer to %s ...\n" % r.name
		if cls.trade_accept(sender_trade_box, r) is False:
			print 'Trade declined.'
			return
		receiver_trade_box = cls.trade_box(r)

		# confirm
		sc, rc = cls.trade_confirm(sender_trade_box, receiver_trade_box)

		# trade
		if (sc and rc) == 'y':
			print "Processing ... one moment."
			for prop in sender_trade_box['properties']:
				r.properties[prop.name] = s.properties[prop.name]
				cls.board.tiles[prop.name]['owner'] = r.name
				del s.properties[prop.name]

			s.money -= sender_trade_box['money']
			r.money += sender_trade_box['money']

			for prop in receiver_trade_box['properties']:
				s.properties[prop.name] = r.properties[prop.name]
				cls.board.tiles[prop.name]['owner'] = s.name
				del r.properties[prop.name]

			s.money += receiver_trade_box['money']
			r.money -= receiver_trade_box['money']

			# Log transaction
			print 'Transaction Complete - see log'

			m1 = sender_trade_box['money']
			m2 = receiver_trade_box['money']
			i1 = [prop.name for prop in sender_trade_box['properties']]
			i2 = [prop.name for prop in receiver_trade_box['properties']]

			GameLogger.add_log(msgtype='trade', p1=s.name, p2=r.name, i1=i1, m1=m1, i2=i2, m2=m2)
			return
		print "Trade has been rejected."
		return

	@classmethod
	def trade_box(cls, player):

		''' Displays a series of menus to coordinate
		a trade between two players. Since this is the command-line
		version, it's not optimal - but it works!
		'''

		player_trade_box = {'name': player.name, 'money': 0, 'properties': []}

		ongoing_s = True
		# Sender
		while ongoing_s:

			print "What would you like to trade? >"
			choice = raw_input(" (0: Properties 1: Money 2: Passes 3: Confirm 4: Start Over 5: Cancel) > ")

			# trading properties
			if choice == '0':
				player_menu = {}
				# loading up items to trade
				for i, prop in enumerate(player.properties.values()):
					print "\t %s : %s" % (i, ansi_tile_display(prop.name))
					player_menu[str(i)] = prop
				print "\t %s : Back" % len(player.properties)
				player_menu[len(player.properties)] = "Back"
				menu_choice = raw_input(">> ")

				if menu_choice == str(len(player.properties)):
					print "\t Back to trade menu ..."
					continue
				item = player_menu[menu_choice]
				if item in player_trade_box['properties']:
					print "Removing %s from trade box." % item.name
					player_trade_box['properties'].remove(item)
					continue

				print "Adding '%s' to trade box ..." % item.name
				player_trade_box['properties'].append(item)
				continue

			# trading money
			elif choice == '1':
				money_offer = False
				while not money_offer:
					money = raw_input("How much money would you like to trade? > ")
					if not money.isdigit():
						print '\t Not valid amount.'
						continue
					money = int(money)
					if (player.money - money) < 0:
						print "\t Not enough money."
					else:
						player_trade_box['money'] += int(money)
						print "Loaded $%s to trade box ..." % money
						money_offer = True

			# offer confirmation
			elif choice == '3':
				print "You're about to trade: "
				print "\t Money: "
				print "\t - $%s" % player_trade_box['money']
				print "\t Properties: "
				for prop in player_trade_box['properties']:
					print "\t -", prop.name
				offer = raw_input("Can you confirm this offer? (y/n) > ").lower()
				if offer == 'y':
					ongoing_s = False
				elif offer == 'n':
					continue
				else:
					ongoing_s = False

			# Start over
			elif choice == '4':
				print "Clearing trade box ..."
				player_trade_box['properties'] = []
				player_trade_box['money'] = 0
				continue

			# Cancel Trade
			elif choice == '5':
				print "Cancelling Trade ..."
				ongoing_s = False
				return

		return player_trade_box

	@classmethod
	def trade_accept(cls, s_trade_box, r):

		print "'%s' would like to trade: " % s_trade_box['name']
		if s_trade_box['properties']:
			print "Properties:"
			for prop in s_trade_box['properties']:
				print "- ", ansi_tile_display(prop.name)
		if s_trade_box['money']:
			print "Money: $%s \n" % s_trade_box['money']

		offer_reaction = raw_input("Do you want to respond to their offer? (y/n) > ").lower()
		if offer_reaction == 'y':
			print "Trade has been accepted by %r." % r.name
			return True
		else:
			return False

		# Final confirmation, exchange of trade boxes.

	@classmethod
	def trade_confirm(cls, sender_trade_box, receiver_trade_box):
		# Sender
		print ("_" * 20) + " SUMMARY " + (20 * "_")
		print "'%s' is trading: " % (sender_trade_box['name'])
		print "Properties:"
		for prop in sender_trade_box['properties']:
			print "- ", ansi_tile_display(prop.name)
		print "Money: $%s \n" % sender_trade_box['money']

		# Receiver
		print "... For '%s's': " % (receiver_trade_box['name'])
		print "Properties:"
		for prop in receiver_trade_box['properties']:
			print "- ", ansi_tile_display(prop.name)
		print "Money: $%s \n" % receiver_trade_box['money']

		s_confirm = raw_input("%s, is this okay? (y/n)" % sender_trade_box['name']).lower()
		r_confirm = raw_input("%s, is this okay? (y/n)" % receiver_trade_box['name']).lower()
		return s_confirm, r_confirm

	@classmethod
	def card_event(cls, player, current_location):
		''' Carries out effects from Chance and Community Chest cards.'''

		db = DbInterface()
		p = cls.players[player]
		with db.conn as conn:
			# select a card from top of the deck
			card = cls.cards.select(current_location.lower())
			if db.card_info(conn, current_location, card):
				received_card = db.card_info(conn, current_location, card)
			print "Drew card: ", card
			print "-- ", received_card.description
			GameLogger.add_log(msgtype='card event', name=p.name, card=card, desc=received_card.description)
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
					GameLogger.add_log(msg=msg)

				# assessed for street repairs
				elif received_card.tag == "STRRP":
					print "You own %s houses, and %s hotels" % (assets['houses'], assets['hotels'])
					p.money -= (assets['houses'] * 40)
					p.money -= (assets['hotels'] * 115)
					msg = "'%s' paid $%s and $%s for repairs to houses and hotels, respectively." % (p.name,
													assets['houses'] * 25, assets['hotels'] * 100)
					GameLogger.add_log(msg=msg)

				# you have been elected chairman of the board
				elif received_card.tag == "CHBRD":
					for other in p.others:
						p.money -= received_card.effect
						other.money += received_card.effect
					msg = "'%s' received $%s from other players." % (p.name,
											len(p.others) * received_card.effect)
					GameLogger.add_log(msg=msg)

				# grand opera night
				elif received_card.tag == "GRDON":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect
					msg = "'%s' received $%s from other players." % (p.name, 
											len(p.others) * received_card.effect)
					GameLogger.add_log(msg=msg)

				# it is your birthday
				elif received_card.tag == "YBDAY":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect
					msg = "'%s' received $%s from other players." % (p.name,
											len(p.others) * received_card.effect)
					GameLogger.add_log(msg=msg)

				# normal 'Money' card
				else:
					p.money += received_card.effect
					msg = "'%s' gained $%s." % (p.name, received_card.effect)
					GameLogger.add_log(msg=msg)

				return p.post_interact(cls.board, cls.bank)
			if received_card.category == "move":

				# Go to jail
				if received_card.tag == "GOTOJ":
					p.position = received_card.effect
					p.jail = True
					p.jail_duration = 3
					msg = "'%s' went to '%s'." % (p.name, 'Jail')
					GameLogger.add_log(msg=msg)
					p.post_interact(cls.board, cls.bank)

				# Go back 3 spaces
				elif received_card.tag == "GOBTS":
					p.position += received_card.effect
					print "You've now on ...", cls.board.layout[p.position]
					current_location = cls.board.layout[p.position]
					msg = "'%s' moved back 3 spaces to '%s'." % (p.name, current_location)
					GameLogger.add_log(msg=msg)
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
					GameLogger.add_log(msg=msg)

					if current_location in p.properties:
						print "You already own this property."
						return

					for other in p.others:
						if current_location in other.properties:
							rent = cls.bank.rent_table[p.position]['rent'] * 2
							p.money -= rent
							other.money += rent
							print "You owe %s $%s in rent." % (other.name, rent)
							GameLogger.add_log(msgtype=rent, p1=p.name,
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
					GameLogger.add_log(msg=msg)

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
							GameLogger.add_log(msgtype=rent, p1=p.name, 
											p2=other.name, m=((die1 + die2) * 10))

					p.purchase(cls.board,
						       cls.bank.all_properties[current_location],
						       cls.bank)
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
				GameLogger.add_log(msg=msg)
				p.post_interact(cls.board, cls.bank)
