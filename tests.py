''' organize using some kind of testing module at some point

Consider using unittest module, for now use assertion tests.
'''

# board layout - mechanics
# see if making a full revolution based on
# math works.

from models import Board
from config import DEFAULT_TILES

b = Board(DEFAULT_TILES, None)
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

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)
test_player = Player('tester', b, c)

b.tiles['Oriental Avenue']['owner'] = test_player.name
b.tiles['New York Avenue']['owner'] = test_player.name

assert b.tiles['Oriental Avenue']['owner'] == 'tester'
assert b.tiles['New York Avenue']['owner'] == 'tester'
print "TEST CHECK - Property Ownership works! - PASS"

# tile mechanics - tracking hotels & houses

from models import Board, Cards, Player
from config import CHANCE, COMMUNITY_CHEST
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)
test_player = Player('tester', b, c)
db = dbInterface()
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

c = Cards(CHANCE, COMMUNITY_CHEST)
c.shuffle_cards()
ctop_of_deck = c.chance
cctop_of_deck = c.communitychest
for i in range(16):
	c.select("chance")
	c.select("community chest")
assert c.chance == ctop_of_deck
assert c.communitychest == cctop_of_deck
print "TEST CHECK - Card Shuffling Works! - PASS"

# card mechanics - Make General Repairs and Assessed for street repairs

# card mechanics - monopoly detection
from models import Board, Cards, Bank


b = Board(DEFAULT_TILES, None)
c = Cards(COMMUNITY_CHEST, CHANCE)

x = Player('Noah', b, c)
y = Player('Ev', b, c)
z = Player('Jack', b, c)
players = {'Noah': x, 'Ev': y, 'Jack': z}

db = dbInterface()
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

# database - test dbInterface.card_info()
from db import *

db = dbInterface()
with db.conn as conn:	
	card = db.card_info(conn, "CHANCE", "Take a Trip to Reading Railroad")
	assert card.name == "take a trip to reading railroad"
	assert card.effect == 5
print "TEST CHECK - Card info interface works (dB connection a success!) - PASS"

# player mechanics - interact()
from models import Board, Cards, Player, Bank
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

# player mechanics - Building Assets
from models import Board, Cards, Bank
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

db = dbInterface()
with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'States Avenue'), bank)
	test_player.purchase(b, db.property_info(conn, 'Mediterranean Avenue'), bank)	
	test_player.purchase(b, db.property_info(conn, 'Baltic Avenue'), bank)			
	test_player.purchase(b, db.property_info(conn, 'Water Works'), bank)	
	

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
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)

test_player = Player("test", b, c)
test_player1 = Player("test1", b, c)

bank = Bank(b, {'test': test_player, 'test1': test_player1})

db = dbInterface()

with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'Electric Company'), bank)		
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



