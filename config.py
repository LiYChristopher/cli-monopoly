''' All the game tiles, sorted into categories. These are used during
the instantiation of essential game objects,
like the Board or Interactor.card_event. '''

DEFAULT_TILES = [["Go", "Mediterranean Avenue", "Community Chest", "Baltic Avenue",
					"Income Tax", "Reading Railroad", "Oriental Avenue", "Chance",
					"Vermont Avenue", "Connecticut Avenue", "Visiting/Jail"],
				["St. Charles Place", "Electric Company", "States Avenue",
					"Virginia Avenue", "Pennsylvania Railroad", "St. James Place",
					"Community Chest", "Tennessee Avenue", "New York Avenue", 'Free Parking'],
				['Kentucky Avenue', 'Chance', 'Indiana Avenue', 'Illinois Avenue',
					'B&O Railroad', 'Atlantic Avenue', 'Ventnor Avenue',
					'Water Works', 'Marvin Gardens', 'Go to Jail'],
				['Pacific Avenue', 'North Carolina Avenue', 'Community Chest',
					'Pennsylvania Avenue', 'Short Line', 'Chance',
					'Park Place', 'Luxury Tax', 'Boardwalk']]


CHANCE = ['Advance to Go', 'Advance to Illinois Ave.', 'Advance to St. Charles Place',
			'Advance to nearest Utility', 'Advance to nearest Railroad', 'Advance to nearest Railroad',
			'Bank pays you dividend of $50', 'Get out of Jail Free', 'Go Back 3 Spaces',
			'Go to Jail', 'Make General Repairs', 'Pay poor tax of $15', 'Take a trip to Reading Railroad',
			'Take a walk on the Boardwalk', 'You have been elected Chairman of the Board',
			'Your building and loan matures', 'You have won a crossword competition']

COMMUNITY_CHEST = ['Advance to Go', 'Bank error in your favor', 'Doctor\'s Fees',
					'From sale of stock you get $50', 'Get Out of Jail Free',
					'Go to Jail', 'Grand Opera Night', 'Holiday Fund matures',
					'Income Tax Refund', 'It is your Birthday', 'Life Insurance Matures',
					'Receive $25 consultancy fee', 'Assessed for street repairs',
					'You have won second prize in a beauty contest', 'You inherit $100']

NON_PROPS = ['Go', 'Visiting/Jail', 'Free Parking',
				'Go to Jail', 'Income Tax', 'Luxury Tax']

GAME_CARDS = ['Chance', 'Community Chest']

UPGRADEABLE = ["Mediterranean Avenue", "Baltic Avenue", "Oriental Avenue",
				"Vermont Avenue", "Connecticut Avenue", "St. Charles Place",
				"States Avenue", "Virginia Avenue", "St. James Place",
				"Tennessee Avenue", "New York Avenue", 'Kentucky Avenue',
				'Indiana Avenue', 'Illinois Avenue', 'Atlantic Avenue', 'Ventnor Avenue',
				'Marvin Gardens', 'Pacific Avenue', 'North Carolina Avenue',
				'Pennsylvania Avenue', 'Park Place', 'Boardwalk']

NON_UPGRADEABLE = ["Reading Railroad", "Electric Company", "Pennsylvania Railroad",
					"B&O Railroad", "Water Works", "Short Line"]

# for DBless version in the future
PROPERTIES_RAW = [('Mediterranean Avenue', 'purple', 60, 2, 30, 10, 30, 90, 160, 250),
					('Baltic Avenue', 'purple', 60, 4, 30, 20, 60, 180, 320, 450),
					('Reading Railroad', 'rr', 200, 25, 100, None, None, None, None, None),
					('Oriental Avenue', 'periwinkle', 100, 6, 50, 30, 90, 270, 400, 550),
					('Vermont Avenue', 'periwinkle', 100, 6, 50, 30, 90, 270, 400, 550),
					('Connecticut Avenue', 'periwinkle', 120, 8, 60, 40, 100, 300, 450, 600),
					('St. Charles Place', 'magenta', 140, 10, 70, 50, 150, 450, 625, 750),
					('Electric Company', 'utility', 150, 4, 75, None, None, None, None, None),
					('States Avenue', 'magenta', 140, 10, 70, 50, 150, 450, 625, 750),
					('Virginia Avenue', 'magenta', 160, 12, 80, 60, 180, 500, 700, 900),
					('Pennsylvania Railroad', 'rr', 200, 25, 100, None, None, None, None, None),
					('St. James Place', 'orange', 180, 14, 90, 70, 200, 550, 750, 950),
					('Tennessee Avenue', 'orange', 180, 14, 90, 70, 200, 550, 750, 950),
					('New York Avenue', 'orange', 200, 16, 100, 80, 220, 600, 800, 100),
					('Kentucky Avenue', 'red', 220, 18, 100, 90, 250, 700, 875, 1050),
					('Indiana Avenue', 'red', 220, 18, 110, 90, 250, 700, 875, 1050),
					('Illinois Avenue', 'red', 240, 20, 120, 100, 300, 750, 925, 1100),
					('B&O Railroad', 'rr', 200, 25, 100, None, None, None, None, None),
					('Atlantic Avenue', 'yellow', 260, 22, 130, 110, 330, 800, 975, 1150),
					('Ventnor Avenue', 'yellow', 260, 22, 130, 110, 330, 800, 975, 1150),
					('Marvin Gardens', 'yellow', 280, 24, 140, 120, 360, 850, 1025, 1200),
					('Pacific Avenue', 'green', 300, 26, 150, 130, 390, 900, 1100, 1275),
					('North Carolina Avenue', 'green', 300, 26, 150, 130, 390, 900, 1100, 1275),
					('Pennsylvania Avenue', 'green', 320, 28, 160, 150, 450, 1000, 1200, 1400),
					('Short Line', 'rr', 200, 25, 100, None, None, None, None, None),
					('Park Place', 'blue', 350, 35, 175, 175, 600, 1100, 1300, 1500),
					('Boardwalk', 'blue', 400, 50, 200, 200, 600, 1400, 1700, 2000),
					('Water Works', 'utility', 150, 4, 75, None, None, None, None, None)
					]
