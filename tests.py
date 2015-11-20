''' organize using some kind of testing module at some point'''

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

# card mechanics - Make General Repairs and Assessed for street repairs



# database - test dbInterface.card_info()
from db import *

db = dbInterface()
with db.conn as conn:	
	card = db.card_info(conn, "CHANCE", "Take a Trip to Reading Railroad")
	assert card.name == "take a trip to reading railroad"
	assert card.effect == 5


# player mechanics - already owning a card
from models import Board, Cards, Player, Bank
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)
bank = Bank()

test_player = Player("test", b, c)
bank.balances[test_player.name] = 0
db = dbInterface()
with db.conn as conn:
	prop1 = db.property_info(conn, 'Oriental Avenue')
	test_player.properties[prop1.name] = prop1
	b.tiles[prop1.name]['owner'] = test_player.name
assert test_player.interact(b, bank, "Oriental Avenue") == None #just check that prop is already owned

# player mechanics - Building Assets
from models import Board, Cards, Bank
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)
test_player = Player('tester', b, c)
bank = Bank()
db = dbInterface()
with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'States Avenue'), Bank())
	test_player.purchase(b, db.property_info(conn, 'Mediterranean Avenue'), Bank())	
	test_player.purchase(b, db.property_info(conn, 'Baltic Avenue'), Bank())			
	test_player.purchase(b, db.property_info(conn, 'Water Works'), Bank())	
	

prop1 = test_player.properties['Mediterranean Avenue']
prop2 = test_player.properties['Baltic Avenue']
prop3 = test_player.properties['States Avenue']

test_player.build_asset(2, prop1, bank)
assert test_player.board.tiles[prop1.name]['houses'] == 2
assert bank.houses == 30
assert bank.hotels == 12

test_player.build_asset(1, prop1, bank)
assert test_player.board.tiles[prop1.name]['houses'] == 3
assert bank.houses == 29
assert bank.hotels == 12

test_player.build_asset(3, prop1, bank)
assert test_player.board.tiles[prop1.name]['hotels'] == 1
assert bank.houses == 32
assert bank.hotels == 11

test_player.build_asset(3, prop3, bank)
assert test_player.board.tiles[prop3.name]['houses'] == 0
assert bank.houses == 32
assert bank.hotels == 11

test_player.build_asset(3, prop2, bank)
assert test_player.board.tiles[prop2.name]['houses'] == 3
assert bank.houses == 29
assert bank.hotels == 11	

# player mechanics - mortgaging/demortgaging a property
from models import Board, Cards, Bank
from db import dbInterface

b = Board(DEFAULT_TILES, None)
c = Cards(CHANCE, COMMUNITY_CHEST)
test_player = Player('tester', b, c)
bank = Bank()
db = dbInterface()

with db.conn as conn:
	test_player.purchase(b, db.property_info(conn, 'Electric Company'), Bank())		
	prop4 = test_player.properties['Electric Company']

test_player.mortgage_property(prop4)
print test_player.money
assert test_player.money == 1400
assert b.tiles[prop4.name]['mortgaged'] == True

test_player.mortgage_property(prop4)
print test_player.money
assert test_player.money == 1325
assert b.tiles[prop4.name]['mortgaged'] == False

test_player.mortgage_property(prop4)
assert test_player.money == 1400
assert b.tiles[prop4.name]['mortgaged'] == True

