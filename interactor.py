from db import DbInterface
from gamelogger import *

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
	def trade(cls, s, r):

		''' Displays a series of menus to coordinate
		a trade between two players. Since this is the command-line
		version, it's not optimal - but it works!
		'''

		p = cls.players
		
		sender_trade_box = {'money': 0, 'properties': [] }
		receiver_trade_box = {'money': 0, 'properties': [] }

		ongoing_s = True

		# Sender
		while ongoing_s:

			print "What would you like to trade? >"
			choice = raw_input(" (0: Properties 1: Money 2: Passes 3: Confirm 4: Start Over 5: Cancel) > ")
			
			if choice == '0':
				s_menu = {}

				# loading up items to trade
				for i, prop in enumerate(s.properties.values()):
					print "\t %s : %s" % (i, prop.name)
					s_menu[str(i)] = prop
				print "\t %s : Back" % len(s.properties)
				s_menu[len(s.properties)] = "Back"
				menu_choice = raw_input(">> ")

				if menu_choice == str(len(s.properties)):
					print "\t Back to trade menu ..."
					continue
				item = s_menu[menu_choice]
				if item in sender_trade_box['properties']:
					print "Removing %s from trade box." % item.name
					sender_trade_box['properties'].remove(item)
					continue

				print "Adding '%s' to trade box ..." % (item.name)
				sender_trade_box['properties'].append(item)
				continue

			elif choice == '1':
				
				money_offer = False
				while not money_offer:
					money = raw_input("How much money would you like to trade? > ")
					if not money.isdigit():
						print '\t Not valid amount.'
						continue
					money = int(money)
					if (s.money - money) < 0:
						print "\t Not enough money." 
					else:
						sender_trade_box['money'] += int(money)
						print "Loaded $%s to trade box ..." % money
						money_offer = True

			# offer confirmation
			elif choice == '3':
				print "You're about to trade: "
				print "\t Money: "
				print "\t - $%s" % sender_trade_box['money']
				print "\t Properties: " 
				for prop in sender_trade_box['properties']:
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
				sender_trade_box['properties'] = []
				sender_trade_box['money'] = 0
				continue 

			# Cancel Trade
			elif choice == '5':
				print "Cancelling Trade ..."
				ongoing_s = False
				return

		print "Sending offer to %s ..." % r.name
		print "'%s', '%s' has offered their properties:" % (r.name, s.name)
		for prop in sender_trade_box['properties']:
			print "- ", prop.name
		print "and $%s dollars.\n" % sender_trade_box['money']

		offer_reaction = raw_input("Do you accept/decline their offer? (a/d) > ").lower()
		if offer_reaction == 'd':
			print "Trade has been declined by %s." % r.name
			return

		# Receiver	
		ongoing_r = True
		while ongoing_r:
			print "What would you like to trade? >"
			choice = raw_input(" (0:Properties, 1: Money, 2: Passes, 3: Confirm, 4: Cancel) > ")
			
			if choice == '0':
				r_menu = {}

				# loading up items to trade
				for i, prop in enumerate(r.properties.values()):
					print "\t %s : %s" % (i, prop.name)
					r_menu[str(i)] = prop
				print "\t %s : Back" % len(r.properties)
				r_menu[len(r.properties)] = "Back"
				menu_choice = raw_input(">> ")

				if menu_choice == str(len(r.properties)):
					print "\t Back to trade menu ..."
					continue

				elif menu_choice not in r_menu.keys():
					continue 

				item = r_menu[menu_choice]
				if item in receiver_trade_box['properties']:
					print "Removing %s from trade box." % item.name
					receiver_trade_box['properties'].remove(item)
					continue

				print "Adding '%s' to trade box ..." % (item.name)
				receiver_trade_box['properties'].append(item)
				continue

			elif choice == '1':
				
				money_offer = False
				while not money_offer:
					money = raw_input("How much money would you like to trade? > ")
					if not money.isdigit():
						print '\t - Not valid amount.'
						continue
					money = int(money)
					if (s.money - money) < 0:
						print "\t - Not enough money." 
						money_offer = True
					else:
						receiver_trade_box['money'] += int(money)
						print "Loaded $%s to trade box ..." % money
						money_offer = True

			# offer confirmation
			elif choice == '3':
				print "You're about to trade: "
				print "\t Money: "
				print "\t - $%s" % receiver_trade_box['money']
				print "\t Properties: " 
				for prop in receiver_trade_box['properties']:
					print "\t -", prop.name

				offer = raw_input("Can you confirm this offer? (y/n) > ").lower()
				if offer == 'y':
					ongoing_r = False
				elif offer == 'n':
					continue
				else:
					ongoing_r = False

			# Cancel Trade
			elif choice == '4':
				print "Cancelling Trade ..."
				ongoing_r = False			

		# Final confirmation, exchange of trade boxes.
		
		# Sender
		print ("_" * 20) + " SUMMARY " + (20 * "_")
		print "'%s' is trading properties:" % (s.name)
		for prop in sender_trade_box['properties']:
			print "- ", prop.name
		print "and $%s dollars. \n" % sender_trade_box['money']
		
		# Receiver
		print "... For '%s's' properties:" % (r.name)
		for prop in receiver_trade_box['properties']:
			print "- ", prop.name
		print "and $%s dollars.\n" % receiver_trade_box['money']

		s_confirm = raw_input("%s, is this okay? (y/n)" % s.name).lower()
		r_confirm = raw_input("%s, is this okay? (y/n)" % r.name).lower()

		if s_confirm == 'y' and r_confirm == 'y':
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

		GameLogger.add_log(msgtype='trade', p1=s.name, p2=r.name, 
									i1=i1, m1=m1, i2=i2, m2=m2)
		return

	@classmethod
	def card_event(cls, player, current_location):
		''' '''
		db = DbInterface()
		p = cls.players[player]
		with db.conn as conn:
			# select a card from top of the deck
			card = cls.cards.select(current_location.lower())
			if db.card_info(conn, current_location, card):
				received_card = db.card_info(conn, current_location, card)
			print "Drew card: ", card
			print "-- ", received_card.description
			GameLogger.add_log(msgtype='card event', name=p.name, card=card, 
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
					msg = "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
					GameLogger.add_log(msg=msg)

				# grand opera night  
				elif received_card.tag == "GRDON":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					msg =  "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
					GameLogger.add_log(msg=msg)

				# it is your birthday 
				elif received_card.tag == "YBDAY":
					for other in p.others:
						p.money += received_card.effect
						other.money -= received_card.effect					
					msg =  "'%s' received $%s from other players." % (p.name, len(p.others) * received_card.effect)
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
				GameLogger.add_log(msg=msg)
				p.post_interact(cls.board, cls.bank)



