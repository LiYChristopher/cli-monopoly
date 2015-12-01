''' The gamelogger is crucial in maintaining records of events that
have transpired in game. '''

from datetime import datetime
from pytz import timezone
from colorama import Fore, Back, Style, init
import re

init(autoreset=True)

def timestamp_now_local(tz='US/Eastern'):
	''' Constructs timezone appropriate datetime object,
	and localizes it to given timezone (default is EST). '''

	utc = datetime.now(timezone('UTC'))
	local_time = utc.astimezone(timezone('US/Eastern'))
	return local_time


def log_delta(old_time):
	''' Transform a non-naive datetime object into a 'prettified' time delta,
	to be inserted before the beginning of a log.

	Supports: seconds, minutes, hours, days, weeks, months and years. '''

	time_now = timestamp_now_local()
	delta = str(time_now - old_time)
	time_divs = re.search(r'(\d*?)\s?\w*?,?\s?(\d*):(\d*):(\d*)', delta, re.I)

	d, h, m, s = (int(time_digit) if time_digit else 0
					for time_digit in time_divs.groups())

	if s >= 0 and (h < 1 and m < 1):
		return "%ss" % s 			# seconds

	elif m > 0 and (h < 1 and d < 1):
		return "%sm" % m 			# minutes

	elif (0 < h < 24) and d < 1:
		return "%sh" % h 			# hours

	elif 1 <= d < 14:
		return "%sd" % d 			# days

	elif 14 <= d < 30:
		return "%sw" % (d / 7) 		# weeks

	elif 30 <= d < 365:
		return "%smo" % (d / 30) 	# months

	elif 365 <= d:
		return "%sy" % (d / 365) 	# years
	return


class InvalidLogtype(Exception):
	pass


class GameLogger(object):
	''' Logs any: rent-payments, property trades,
	or significant activities for all players.'''

	players = None
	player_logs = None
	valid_types = ['bank', 'turn', 'rent', 'trade', 'dice',
	               'extra', 'basic', 'purchase', 'card event']
	public_logs = []
	history = []

	@classmethod
	def add_log(cls, msgtype='basic', **kwds):
		''' Appends a new log based on game activities. Accepts argument
		'msgtype', which can be: 'turn','rent', 'trade', and 'extra'. '''

		if msgtype not in cls.valid_types:
			raise InvalidLogtype("No message logged - This is not a valid message type.")

		elif msgtype == 'basic':
			msg = kwds['msg']

		elif msgtype == 'turn':
			msg = "'%s' has ended their turn. \n" % kwds['name']

		elif msgtype == 'dice':
			msg = "'%s' rolled: [[%s],[%s]]." % (kwds['name'],
									kwds['d1'], kwds['d2'])

		elif msgtype == 'purchase':
			msg = "'%s' has purchased '%s' for $%s." % (kwds['name'],
									kwds['property'], kwds['cost'])

		elif msgtype == 'rent':
			msg = "'%s' paid '%s' $%s in rent." % (kwds['p1'],
									kwds['p2'], kwds['m'])

		elif msgtype == 'trade':
			msg = "<-> '%s' traded '%s' - '%s' and $%s for '%s' and $%s." % (kwds['p1'], kwds['p2'],
									kwds['i1'], kwds['m1'], kwds['i2'], kwds['m2'])
		elif msgtype == 'card event':
			msg = "// '%s' drew card '%s' -- %s " % (kwds['name'],
									kwds['card'].title(), kwds['desc'])

		publish_ts = timestamp_now_local()
		cls.public_logs.append((publish_ts, msg))
		return

	@classmethod
	def push_public_logs(cls, realtime=False):
		for log in cls.public_logs:
			# turn this into Jinja2 compatible objects in the future
			if realtime:
				print log[1]
			cls.history.append(log)
		cls.public_logs = []

	@classmethod
	def display(cls, max_rows=50):
		''' Displays game log in command-line. '''
		print "-" * 60
		print (" " * 15) + "-G A M E 	L O G S-" + (" " * 15)
		print "-" * 60
		start_idx = len(cls.history) - max_rows
		if start_idx < 0:
			start_idx = 0
		for log in cls.history[start_idx:]:
			ts = log_delta(log[0])
			print "%s ago - %s" % (ts, log[1])
		print "_" * 60
		print "_" * 60
		return


def ansi_tile(tile_name):
	''' Displays property names with appropriate ANSI terminal colors. '''

	colored_out = tile_name

	if tile_name in ['Mediterranean Avenue', 'Baltic Avenue']:
		colored_out = Fore.BLUE + tile_name

	elif tile_name in ['Vermont Avenue', 'Connecticut Avenue', 'Oriental Avenue']:
		colored_out = Style.BRIGHT + Fore.CYAN + tile_name

	elif tile_name in ['St. Charles Place', 'Virginia Avenue', 'States Avenue']:
		colored_out = Style.BRIGHT + Fore.MAGENTA + tile_name

	elif tile_name in ['St. James Place', 'Tennessee Avenue', 'New York Avenue']:
		colored_out = Fore.RED + tile_name

	elif tile_name in ['Kentucky Avenue', 'Indiana Avenue',
							'Illinois Avenue']:
		colored_out = Style.BRIGHT + Fore.RED + tile_name

	elif tile_name in ['Atlantic Avenue', 'Ventnor Avenue', 'Marvin Gardens']:
		colored_out = Style.BRIGHT + Fore.YELLOW + tile_name

	elif tile_name in ['Pacific Avenue', 'North Carolina Avenue',
							'Pennsylvania Avenue']:
		colored_out = Fore.GREEN + tile_name

	elif tile_name in ['Park Place', 'Boardwalk']:
		colored_out = Style.BRIGHT + Fore.BLUE + tile_name

	elif tile_name in ['Reading Railroad', 'Short Line',
							'B&O Railroad', 'Pennsylvania Railroad']:
		colored_out = Style.BRIGHT + Fore.WHITE + tile_name
	else:
		colored_out = Style.NORMAL + Fore.WHITE + tile_name

	return colored_out

if __name__ == '__main__':

	t1 = timezone('US/Eastern').localize(datetime(2015, 11, 22, 12, 20, 00))
	print log_delta(t1)
