
''' Monopoly-Command Line - V.01

- Bugfixes will be ongoing at this point, especially in
interactor.py
- 'Monopoly takes 1 argument - the number of players.'

'''

from monopoly import Monopoly

if __name__ == '__main__':

    monopoly = Monopoly(3)
    monopoly.setup()

    for turn in range(0, 10):
	    monopoly.turn()

    monopoly.summary()
