''' All the game tiles, sorted into categories. These are used during
the instantiation of essential game objects,
like the Board or Interactor.card_event. '''

DEFAULT_TILES = [["Go", "Mediterranean Avenue", "Community Chest", "Baltic Avenue",
					"Income Tax", "Reading Railroad", "Oriental Avenue",
					"Vermont Avenue", "Connecticut Avenue"],
				["Visiting/Jail", "St. Charles Place", "Electric Company", "States Avenue",
					"Virginia Avenue", "Pennsylvania Railroad", "St. James Place",
					"Community Chest", "Tennessee Avenue", "New York Avenue"],
				['Free Parking', 'Kentucky Avenue', 'Chance', 'Indiana Avenue',
					'Illinois Avenue', 'B&O Railroad', 'Atlantic Avenue', 'Ventnor Avenue',
				'Water Works', 'Marvin Gardens'],
				['Go to Jail', 'Pacific Avenue', 'North Carolina Avenue', 'Community Chest',
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
