''' Tests using unittest and mock.

COMPLETED TESTS:
- models.Board
- models.Bank

TO DO:
- models.Player
- models.Cards
- interactor.Interactor
- gamelogger.timestamp_now_local
- gamelogger.log_delta
- gamelogger.GameLogger
- gamelogger.ansi_tile
- db.DbInterface
'''

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
						'Reading Railroad', 'Pennsylvania Railroad']

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
		sample_prop9 = cls.bank.all_properties['Pennsylvania Railroad']

		player_attrs = {'name': 'Test1',
					'properties': {'Mediterranean Avenue': sample_prop1,
									'Boardwalk': sample_prop2,
									'Park Place': sample_prop3,
									'Water Works': sample_prop4,
									'Electric Company': sample_prop5,
									'B&O Railroad': sample_prop6,
									'Short Line': sample_prop7,
									'Reading Railroad': sample_prop8,}}
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

	def test_railroads_rent_three_bank(self):
		''' Bank.railroads_rent() - Own three railroads'''

		self.bank.tiles['B&O Railroad']['owner'] = self.player.name
		self.bank.tiles['Short Line']['owner'] = self.player.name
		self.bank.tiles['Reading Railroad']['owner'] = self.player.name
		self.bank.tiles['Pennsylvania Railroad']['owner'] = None
		self.bank.railroads_rent(self.bank.players)

		after_rr_check1 = self.bank.rent_table['B&O Railroad']['rent']
		after_rr_check2 = self.bank.rent_table['Short Line']['rent']
		after_rr_check3 = self.bank.rent_table['Reading Railroad']['rent']
		after_rr_check4 = self.bank.rent_table['Pennsylvania Railroad']['rent']
		all_rr_check = (after_rr_check1, after_rr_check2, 
								after_rr_check3, after_rr_check4)

		self.assertTrue(all_rr_check == (100, 100, 100, 25))

	def test_railroads_rent_two_bank(self):
		''' Bank.railroads_rent() - Own two railroads '''

		del self.player.properties['B&O Railroad']

		self.bank.tiles['B&O Railroad']['owner'] = self.player.name
		self.bank.tiles['Short Line']['owner'] = self.player.name
		self.bank.tiles['Reading Railroad']['owner'] = self.player.name

		self.bank.railroads_rent(self.bank.players)

		after_rr_check1 = self.bank.rent_table['B&O Railroad']['rent']
		after_rr_check2 = self.bank.rent_table['Short Line']['rent']
		after_rr_check3 = self.bank.rent_table['Reading Railroad']['rent']
		after_rr_check4 = self.bank.rent_table['Pennsylvania Railroad']['rent']
		all_rr_check = (after_rr_check1, after_rr_check2,
								after_rr_check3, after_rr_check4)

		self.assertTrue(all_rr_check == (50, 50, 50, 25))

	def test_railroads_rent(self):
		''' 'Bank.railroads_rent() - Own none '''

		self.bank.railroads_rent(self.bank.players)

		after_rr_check1 = self.bank.rent_table['B&O Railroad']['rent']
		after_rr_check2 = self.bank.rent_table['Short Line']['rent']
		after_rr_check3 = self.bank.rent_table['Reading Railroad']['rent']
		after_rr_check4 = self.bank.rent_table['Pennsylvania Railroad']['rent']
		all_rr_check = (after_rr_check1, after_rr_check2,
								after_rr_check3, after_rr_check4)

		self.assertTrue(all_rr_check == (25, 25, 25, 25))

if __name__ == '__main__':
	unittest.main()
