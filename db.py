''' Connects the game to specific information related
to individual Cards and Properties. '''

import pymysql
from collections import namedtuple


def todb(function):
	''' Database operations wrapper function.'''

	def operate(interface, *args, **kwargs):
		cursor = interface.conn.cursor()
		try:
			cursor.execute("BEGIN")
			req = function(cursor, *args, **kwargs)
			cursor.execute("COMMIT")
		except:
			cursor.execute("ROLLBACK")
			raise
		finally:
			cursor.close()
		return req
	return operate


class DbInterface(object):
	''' Interface for accessing property and tile information from
	the database. '''

	conn = pymysql.connect(host='localhost', port=3306, user='root',
							passwd='uberschall', db='monopoly')

	@todb
	def property_info(self, cursor, property_name):
		''' Queries dB for property name, returns an
		accessible Property tile for use in-game. '''

		cursor.execute("SELECT name, type, cost, rent, mortgage, h1, h2, h3, h4, hotel\
						FROM property WHERE name=%s", property_name)
		result = cursor.fetchone()
		Info = namedtuple('Property', 'name type cost rent mortgage h1 h2 h3 h4 hotel')
		# use collections.namedtuple to produce clean API
		prop = Info(name=result[0], type=result[1], cost=result[2], rent=result[3],
					mortgage=result[4], h1=result[5], h2=result[6],
					h3=result[7], h4=result[8], hotel=result[9])
		return prop

	@todb
	def card_info(self, cursor, card_type, card_name):
		''' Queries dB for type (Chance or Community Chest) and
		card name, returns an accessible Card tile for use in-game. '''

		card_type = card_type.lower()
		card_name = card_name.lower()
		cursor.execute("SELECT tag, type, category, name, description, effect\
						FROM cards WHERE type = %s\
						AND name=%s", (card_type, card_name,))
		result = cursor.fetchone()
		Info = namedtuple('Card', 'tag type category name description effect')
		card = Info(tag=result[0], type=result[1], category=result[2],
					name=result[3], description=result[4],
					effect=result[5])
		return card

	@todb
	def prop_set_length(self, cursor, card_type):
		''' Used by Player.check_monopoly(); returns 'length' of a
		color group, to be compared to by the 'length' of properties
		owned by the player in the same group. '''

		card_type = card_type.lower()
		cursor.execute("SELECT COUNT(name) FROM property WHERE type=%s\
						AND NOT type='utility' AND NOT type='rr'", card_type)
		result = cursor.fetchone()
		return result

	@todb
	def rent_table(self, cursor):
		''' Generates a table to be used in-game for active tracking
		of rent changes. For each property: name, type and default rent. '''

		cursor.execute("SELECT name, type, rent FROM property")

		result = cursor.fetchall()
		return {prop[0]: {'type': prop[1], 'rent': prop[2]}
				for prop in result}
