''' organize using some kind of testing module at some point

Consider using unittest module, for now use assertion tests.
'''

# board layout - mechanics
# see if making a full revolution based on
# math works.

from mock import Mock, MagicMock, patch, PropertyMock
from unittest import TestCase
from models import Board, Cards, Bank, Player
from config import DEFAULT_TILES
from db import DbInterface

class BoardTests(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.board = Board(DEFAULT_TILES)
		cls.board.prop_tiles()['Boardwalk']['owner'] = "Jimmy"

	@classmethod
	def tearDownClass(cls):
		del cls.board

	def test_corners_board_layout(self):
		self.assertEqual([self.board.layout[i] for i in range(0, 40, 10)],
							['Go', 'Visiting/Jail', 'Free Parking', 'Go to Jail'])

	def test_railroads_board_layout(self):
		self.assertEqual([self.board.layout[i] for i in range(5, 40, 10)],
							['Reading Railroad', 'Pennsylvania Railroad', 'B&O Railroad', 'Short Line'])

	def test_endtoend_board_layout(self):
		self.assertEqual([self.board.layout[i] for i in range(0, 40, 39)],
							['Go', 'Boardwalk'])

	def test_length_board_tiles(self):
		''' for proper board length.'''
		self.assertEqual(len(self.board.tiles), 36)

	def test_length_board_prop_tiles(self):
		''' for proper number of developable properties'''
		self.assertEqual(len(self.board.prop_tiles()), 28)

	def test_check_ownership(self):
		''' for functional dictionary - ownership '''
		self.assertEqual(self.board.check_ownership('Boardwalk'), "Jimmy")

class BankTests(TestCase):

	@classmethod
	@patch('models.Player', autospec=True)
	@patch('models.Board', autospec=True)
	def setUpClass(cls, mock_board, mock_player):

		#cls.bank = Bank(mock_board, mock_player)
		from db import DbInterface

		cls.board = mock_board
		cls.player = mock_player

		sample_tiles = ['Boardwalk', 'Park Place',
						'Mediterranean Avenue', 'Baltic Avenue', 'Water Works',
						'Electric Company', 'B&O Railroad', 'Short Line',
						'Reading Railroad']

		board_attrs = {'prop_tiles.return_value': {str(tile): {"owner": None,
						"hotels": 0, "houses": 0, 'mortgaged': False}
							for tile in sample_tiles}}

		cls.board.configure_mock(**board_attrs)

		cls.bank = Bank(cls.board, {'Test1': cls.player})

		sample_prop1 = cls.bank.all_properties['Mediterranean Avenue']
		sample_prop2 = cls.bank.all_properties['Boardwalk']
		sample_prop3 = cls.bank.all_properties['Park Place']

		sample_prop4 = cls.bank.all_properties['Water Works']
		sample_prop5 = cls.bank.all_properties['Electric Company']

		sample_prop6 = cls.bank.all_properties['B&O Railroad']
		sample_prop7 = cls.bank.all_properties['Short Line']
		sample_prop8 = cls.bank.all_properties['Reading Railroad']

		player_attrs = {'name': 'Test1',
					'properties': {'Mediterranean Avenue': sample_prop1,
									'Boardwalk': sample_prop2,
									'Park Place': sample_prop3,
									'Water Works': sample_prop4,
									'Electric Company': sample_prop5,
									'B&O Railroad': sample_prop6,
									'Short Line': sample_prop7,
									'Reading Railroad': sample_prop8}}
		cls.player.configure_mock(**player_attrs)

	def test_rent_table_two_house_bank(self):
		''' Bank.props_with_assets - Mediterranean Avenue + 2 houses '''

		self.bank.tiles['Mediterranean Avenue']['owner'] = self.player.name
		self.bank.tiles['Mediterranean Avenue']['houses'] += 2
		self.bank.props_with_assets(self.bank.players)

		property_obj_val = self.bank.all_properties['Mediterranean Avenue'].h2
		rent_table_val = self.bank.rent_table['Mediterranean Avenue']['rent']

		self.assertTrue(property_obj_val == rent_table_val)

	def test_props_mortgaged_bank(self):
		''' Bank.props_mortgaged - Boardwalk is mortgaged '''

		self.bank.tiles['Boardwalk']['owner'] = self.player.name
		before_mortgage = self.bank.rent_table['Boardwalk']['rent']
		self.bank.tiles['Boardwalk']['mortgaged'] = True

		self.bank.props_mortgaged()
		after_mortgage = self.bank.rent_table['Boardwalk']['rent']

		self.assertFalse(before_mortgage == after_mortgage)

	def test_props_mortgaged_ownerless_bank(self):
		''' Bank.props_mortgaged - No owner '''

		self.bank.tiles['Boardwalk']['owner'] = None
		before_mortgage = self.bank.rent_table['Boardwalk']['rent']
		self.bank.tiles['Boardwalk']['mortgaged'] = True

		self.bank.props_mortgaged()
		after_mortgage = self.bank.rent_table['Boardwalk']['rent']

		self.assertTrue(before_mortgage == after_mortgage)

	def test_props_monopoly_bank(self):
		''' Banks.props_monopoly - Monopoly '''

		before_monopoly_1 = self.bank.rent_table['Boardwalk']['rent']
		before_monopoly_2 = self.bank.rent_table['Park Place']['rent']

		self.player.check_monopoly.return_value = ['blue']
		self.bank.props_monopoly(self.bank.players)

		after_monopoly_1 = self.bank.rent_table['Boardwalk']['rent']
		after_monopoly_2 = self.bank.rent_table['Park Place']['rent']

		self.assertTrue(after_monopoly_1 == before_monopoly_1*2)
		self.assertTrue(after_monopoly_2 == before_monopoly_2*2)

	def test_utilities_rent_bank(self):
		''' Bank.utilities_rent() - Complete ownership ($4 - $10 base)'''

		self.bank.tiles['Electric Company']['owner'] = self.player.name
		self.bank.tiles['Water Works']['owner'] = self.player.name

		before_util_check1 = self.bank.rent_table['Electric Company']['rent']
		before_util_check2 = self.bank.rent_table['Water Works']['rent']

		self.bank.utilities_rent(self.bank.players)

		after_util_check1 = self.bank.rent_table['Electric Company']['rent']
		after_util_check2 = self.bank.rent_table['Water Works']['rent']

		self.assertTrue(after_util_check1 == 10 and after_util_check2 == 10)

	def test_utilities_rent_ownerless_bank(self):
		''' Bank.utilities_rent() - Incomplete ownership ($4 - $10 base)'''

		self.bank.tiles['Electric Company']['owner'] = 'Bob'
		self.bank.tiles['Water Works']['owner'] = self.player.name

		before_util_check1 = self.bank.rent_table['Electric Company']['rent']
		before_util_check2 = self.bank.rent_table['Water Works']['rent']

		self.bank.utilities_rent(self.bank.players)

		after_util_check1 = self.bank.rent_table['Electric Company']['rent']
		after_util_check2 = self.bank.rent_table['Water Works']['rent']

		self.assertTrue(after_util_check1 == 4 and after_util_check2 == 4)

	def test_railroads_rent_bank(self):
		
		pass

'''
b = Board(DEFAULT_TILES)
endpoint = b.layout.index('Reading Railroad')
pos = 1
circuit_dist = (40 - pos) + endpoint
pos += circuit_dist
pos %= 40
print b.layout[pos]
assert b.layout[endpoint] == b.layout[pos]


# tile mechanics - new owner for property
from models import Board, Cards, Player
from config import CHANCE, COMMUNITY_CHEST

b = Board(DEFAULT_TILES)
c = Cards()
test_player = Player('tester', b, c)

b.tiles['Oriental Avenue']['owner'] = test_player.name
b.tiles['New York Avenue']['owner'] = test_player.name

assert b.tiles['Oriental Avenue']['owner'] == 'tester'
assert b.tiles['New York Avenue']['owner'] == 'tester'
print "TEST CHECK - Property Ownership works! - PASS"

# tile mechanics - tracking hotels & houses

from models import Board, Cards, Player
from config import CHANCE, COMMUNITY_CHEST
from db import DbInterface

b = Board(DEFAULT_TILES)
c = Cards()
test_player = Player('tester', b, c)
db = DbInterface()
with db.conn as conn:
	prop1 = db.property_info(conn, 'Oriental Avenue')
	prop2 = db.property_info(conn, 'New York Avenue')
	b.tiles['Oriental Avenue']['owner'] = test_player.name
	test_player.properties[prop1.name] = prop1
	b.tiles['New York Avenue']['owner'] = test_player.name
	test_player.properties[prop2.name] = prop2

b.tiles['Oriental Avenue']['hotels'] += 1
b.tiles['New York Avenue']['houses'] += 1
b.tiles['New York Avenue']['hotels'] += 1
total_houses = 0
total_hotels = 0

for prop in test_player.properties:
	total_houses += test_player.board.tiles[prop]['houses']
	total_hotels += test_player.board.tiles[prop]['hotels']

assert total_houses == 1
assert total_hotels == 2
assert b.tiles['Oriental Avenue']['houses'] == 0
assert b.tiles['New York Avenue']['houses'] == 1
print "TEST CHECK - Asset acquisition works! - PASS"

# cards mechanics - moving cards to bottom of deck
from models import Cards
from config import CHANCE, COMMUNITY_CHEST

c = Cards()
c.shuffle_cards()
ctop_of_deck = c.chance
cctop_of_deck = c.communitychest
for i in range(16):
	c.select("chance")
	c.select("community chest")
assert c.chance == ctop_of_deck
assert c.communitychest == cctop_of_deck
print "TEST CHECK - Card Shuffling Works! - PASS"

# card mechanics - all community chest
from models import Cards, Player, Board, Bank
from config import CHANCE, COMMUNITY_CHEST
from interactor import Interactor

c = Cards()
b = Board(DEFAULT_TILES)

x = Player('test', b, c)
bank = Bank(b, {'test': x})
Interactor.players = {'test': x}
Interactor.board = b
Interactor.bank = bank
Interactor.cards = c

for i in range(17):
	print "PLAYER's current location BEFORE", x.current_position()
	x.interact('Chance', b, bank)
	print "PLAYER's current location AFTER\n\n", x.current_position()

print "TEST CHECK - All Chance cards"

for i in range(17):
	print "PLAYER's current location BEFORE", x.current_position()
	x.interact('Community Chest', b, bank)
	print "PLAYER's current location AFTER\n\n", x.current_position()

print "TEST CHECK - All Community Chest cards"

# card mechanics - monopoly detection
from models import Board, Cards, Bank

b = Board(DEFAULT_TILES)
c = Cards()

x = Player('Noah', b, c)
y = Player('Ev', b, c)
z = Player('Jack', b, c)
players = {'Noah': x, 'Ev': y, 'Jack': z}

db = DbInterface()
with db.conn as conn:
	prop1a = db.property_info(conn, 'Reading Railroad',)
	prop1b = db.property_info(conn, 'B&O Railroad', )
	prop1c = db.property_info(conn, 'Short line', )
	prop1d = db.property_info(conn, 'Pennsylvania Railroad', )

	prop2a = db.property_info(conn, 'St. Charles Place', )
	prop2b = db.property_info(conn, 'States Avenue', )
	prop2c = db.property_info(conn, 'Virginia Avenue', )

	prop3 = db.property_info(conn, 'Electric Company')
	prop4 = db.property_info(conn, 'Water Works')

bank = Bank(b, players)

# ACQUISITIONS ROUND 1
z.properties['Reading Railroad'] = prop1a
b.tiles['Reading Railroad']['owner'] = z.name

z.properties['B&O Railroad'] = prop1b
b.tiles['B&O Railroad']['owner'] = z.name

x.properties['St. Charles Place'] = prop2a
b.tiles['St. Charles Place']['owner'] = x.name

bank.update_all_rents(players)

assert bank.rent_table['Electric Company']['rent'] == 4
assert bank.rent_table['B&O Railroad']['rent'] == 50
assert bank.rent_table['St. Charles Place']['rent'] == 10
print "TEST CHECK - Rent Updates > Acquisition Round 1 - PASS"

# ACQUISITIONS ROUND 2
y.properties['Electric Company'] = prop3
b.tiles['Electric Company']['owner'] = y.name

z.properties['Short Line'] = prop1c
b.tiles['Short Line']['owner'] = z.name

y.properties['Water Works'] = prop4
b.tiles['Water Works']['owner'] = y.name

bank.update_all_rents(players)

assert bank.rent_table['Electric Company']['rent'] == 10
assert bank.rent_table['Short Line']['rent'] == 100
assert bank.rent_table['St. Charles Place']['rent'] == 10
print "TEST CHECK - Rent Updates > Acquisition Round 2 - PASS"

# ACQUISITIONS ROUND 3
x.properties['States Avenue'] = prop2b
b.tiles['States Avenue']['owner'] = x.name

x.properties['Virginia Avenue'] = prop2c
b.tiles['Virginia Avenue']['owner'] = x.name

z.properties['Pennsylvania Railroad'] = prop1d
b.tiles['Pennsylvania Railroad']['owner'] = z.name	

bank.update_all_rents(players)

assert bank.rent_table['Water Works']['rent'] == 10
assert bank.rent_table['Pennsylvania Railroad']['rent'] == 200
assert bank.rent_table['St. Charles Place']['rent'] == 20
print "TEST CHECK - Rent Updates > Acquisition Round 3 - PASS"

bank.update_all_rents(players)

assert x.check_monopoly() == ['magenta']
print "TEST CHECK - Monopoly Check > Acquisition Round 3 - PASS"

# database - test DbInterface.card_info()
from db import *

db = DbInterface()
with db.conn as conn:	
	card = db.card_info(conn, "CHANCE", "Take a Trip to Reading Railroad")
	assert card.name == "take a trip to reading railroad"
	assert card.effect == 5
print "TEST CHECK - Card info interface works (dB connection a success!) - PASS"

# player mechanics - interact()
from models import Board, Cards, Player, Bank
from db import DbInterface

b = Board(DEFAULT_TILES)
c = Cards()

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

# player mechanics - Building Assets
from models import Board, Cards, Bank
from db import DbInterface

b = Board(DEFAULT_TILES)
c = Cards()

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

db = DbInterface()
with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'States Avenue'))
	test_player.purchase(b, db.property_info(conn, 'Mediterranean Avenue'))
	test_player.purchase(b, db.property_info(conn, 'Baltic Avenue'))
	test_player.purchase(b, db.property_info(conn, 'Water Works'))


prop1 = test_player.properties['Mediterranean Avenue']
prop2 = test_player.properties['Baltic Avenue']
prop3 = test_player.properties['States Avenue']

test_player.build_asset(2, prop1, bank)
assert test_player.board.tiles[prop1.name]['houses'] == 2
assert bank.houses == 30
assert bank.hotels == 12
print "TEST CHECK - Purchasing of properties work! (I) - PASS"

test_player.build_asset(1, prop1, bank)
assert test_player.board.tiles[prop1.name]['houses'] == 3
assert bank.houses == 29
assert bank.hotels == 12
print "TEST CHECK - Purchasing of properties work! (II) - PASS"

test_player.build_asset(3, prop1, bank)
assert test_player.board.tiles[prop1.name]['hotels'] == 1
assert bank.houses == 32
assert bank.hotels == 11
print "TEST CHECK - Purchasing of properties work! (III) - PASS"

test_player.build_asset(3, prop3, bank)
assert test_player.board.tiles[prop3.name]['houses'] == 0
assert bank.houses == 32
assert bank.hotels == 11
print "TEST CHECK - Purchasing of properties work! (IV) - PASS"

assert test_player.board.tiles[prop2.name]['houses'] == 0
assert bank.houses == 32
assert bank.hotels == 11
print "TEST CHECK - Purchasing of properties work! (V) - PASS"

# player mechanics - mortgaging/demortgaging a property
from models import Board, Cards, Bank
from db import DbInterface

b = Board(DEFAULT_TILES)
c = Cards()

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

db = DbInterface()

with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'Electric Company'))
	prop4 = test_player.properties['Electric Company']

test_player.mortgage_property(prop4, bank)
print test_player.money
assert test_player.money == 1400
assert b.tiles[prop4.name]['mortgaged'] == True
print "TEST CHECK - Initial Mortgaging works! - PASS"

test_player.mortgage_property(prop4, bank)
print test_player.money
assert test_player.money == 1325
assert b.tiles[prop4.name]['mortgaged'] == False
print "TEST CHECK - Demortgaging works! (same func) - PASS"

test_player.mortgage_property(prop4, bank)
assert test_player.money == 1400
assert b.tiles[prop4.name]['mortgaged'] == True
print "TEST CHECK - Once again mortgaging - PASS"
'''

if __name__ == '__main__':
	unittest.main()

