from models import *
from db import *
from engine import *


if __name__ == '__main__':
	game = Engine(3)

	game.setup()

	for turn in range(0, 10):
		game.turn()

	game.summary()