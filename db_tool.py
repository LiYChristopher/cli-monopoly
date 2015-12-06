''' Short scripts to help load the SQL database with essential game components
namely the Cards and Properties. '''

from db import dbInterface
import csv

def csvtosql_cards(csvfile):
	''' Loads SQL Database with Cards info.'''
	db = dbInterface()
	with open(csvfile, "rU") as to_read:
		reader = csv.reader(to_read)
		with db.conn as conn:
			cursor = conn.cursor()
			reader.next()
			for row in reader:
				row[0] = int(row[0])
				row[4] = row[4].lower()
				row[6] = int(row[6])
				row = tuple(row)
				cursor.execute("INSERT INTO cards(id, tag, type, category, name, description, effect)\
								VALUES(%s, %s, %s, %s, %s, %s, %s)", row)
				conn.commit()
		cursor.close()
	return "Database has been loaded."

if __name__ == '__main__':
	print csvtosql_cards('cards.csv')
