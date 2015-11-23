
from datetime import datetime
import time
from pytz import timezone
import re

def timestamp_now_local(tz='US/Eastern'):
	''' Constructs timezone appropriate datetime object,
	and localizes it to given timezone (default is EST).'''

	current_time = datetime.utcnow()
	fmt = "%m-%d-%Y %H:%M:%S"
	ts = timezone('US/Eastern').localize(current_time)
	utc = datetime.now(timezone('UTC'))
	local_time = utc.astimezone(timezone('US/Eastern'))
	return local_time

def log_delta(old_time):
	''' Transform a non-naive datetime object into a 'prettified' time delta,
	to be inserted before the beginning of a log. 

	Supports: seconds, minutes, hours, days, weeks, months and years.
	'''

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

class gameLogger(object):
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
			msg = "'%s' rolled: [[%s],[%s]]." % (kwds['name'], kwds['d1'], kwds['d2']) 
		
		elif msgtype == 'purchase':
			msg = "'%s' has purchased '%s' for $%s." % (kwds['name'], kwds['property'], kwds['cost'])
		
		elif msgtype == 'rent':
			msg = "'%s' paid '%s' $%s in rent." % (kwds['p1'], kwds['p2'], kwds['m'])
		
		elif msgtype == 'trade':
			msg = "<-> '%s' traded '%s' - '%s' and $%s for '%s' and $%s." % (kwds['p1'], kwds['p2'], 
													kwds['i1'], kwds['m1'], kwds['i2'], kwds['m2'])
		elif msgtype == 'card event':
			msg = "// '%s' drew card '%s' -- %s " % (kwds['name'], kwds['card'].title(), kwds['desc'])
		
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



if __name__ == '__main__':

	t1 = timezone('US/Eastern').localize(datetime(2015, 11, 22, 12, 20, 00))
	print log_delta(t1)
	
