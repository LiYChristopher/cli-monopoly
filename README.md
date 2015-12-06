This is a command-line version of Hasbro's Monopoly, implemented in Python.

The intent in making an implementation of this game is to put it online via a
web framework, most likely Flask, so people can play and interact with each other in real-time. The first step of course
was making the foundation of the game - which for the most part is done now. 

At the moment the game only runs via the command-line with the run.py file. More info below.
It also has a SQL dependency (since I intended to put this online), so I need to write a workaround
so that it can work without needing to do a DB look up on info associated with Properties and Cards.

This is my first solo project, so the API is probably not perfect, but I gained a lot of valuable experience
in object-oriented development, working with a third-party python SQL library and writing some unit tests.

To Dos:

- Finish post-interaction menu; mortgage property function is complete, but not implemented
into the menu yet.

- Detection of bankruptcy; the game currently doesn't react if a player is bankrupt, which in
this implementation means that their money deficit after a turn is greater than the total 
value of their non-money assets - houses, hotels and properties (mortgage values).

- Player option to forfeit; there's no such option yet.

Looking Forward:

- Working on integrating this framework into a web-app using Flask.
- Reimplementing with ncurses/npyscreen - to achieve an improved user experience and aesthetic, I wanted to achieve
within the command-line.

Getting Started:

Coming soon ...