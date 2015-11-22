



class InvalidLogtype(Exception):
	pass

class gameLogger(object):
	''' Logs any: rent-payments, property trades,
	or significant activities for all players.'''

	players = None
	player_logs = None
	valid_types = ['bank', 'turn', 'rent', 'trade', 
					'dice', 'extra', 'basic', 'purchase']
	public_logs = []

	def __init__(self, max_record=500):
		pass

	@classmethod
	def add_log(cls, msgtype=None, **kwds):
		''' Appends a new log based on game activities. Accepts argument
		'msgtype', which can be: 'turn','rent', 'trade', and 'extra'. '''

		if msgtype not in cls.valid_types:
			raise InvalidLogtype("No message logged - This is not a valid message type.")
		elif msgtype == 'basic':
			msg = kwds['msg']
		elif msgtype == 'turn':
			msg = "'%s' has ended their turn." % kwds['name']
		elif msgtype == 'dice':
			msg = "'%s' rolled: [[%s],[%s]]" % (kwds['name'], kwds['d1'], kwds['d2']) 
		elif msgtype == 'purchase':
			msg = "'%s' has purchased %s for $%s" % (kwds['name'], kwds['property'], kwds['cost'])
		elif msgtype == 'rent':
			msg = "'%s' paid '%s' $%s in rent." % (kwds['p1'], kwds['p2'], kwds['m'])
		elif msgtype == 'trade':
			msg = "'%s' --> '%s' - traded %s for %s." % (kwds['p1'], kwds['p2'], 
													kwds['i1'], kwds['i2'])
		cls.public_logs.append(msg)
		return

	@classmethod
	def push_public_logs(cls):
		for log in cls.public_logs:
			# turn this into Jinja2 compatible objects in the future
			print "// ...", log
		cls.public_logs = []