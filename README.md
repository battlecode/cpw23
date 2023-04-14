# Battlecode-o7

# Game Rules

Battlecode-o7 is a two player game based on the popular hand game, [007 (also known as James Bond or Standoff)](https://ludocity.org/wiki/Standoff_(hand_game)).

In our version, each player controls 3 bots and each bot has 5 health. 

The game plays out as a series of rounds. 

In each round, all bots simultaneously act out one of three choices:
* Attack an opponent with some amount of ammo
* Load one ammo
* Shield
    - Gain a temporary 3 health for this turn. Attacks performed on this bot will first drain shield health and then bot health.

After the round ends, bots with 0 health can take no further actions.

# Installation Instructions

**Please ask any of us for help if you're having issues of if you're confused!**

Download [Python 3](https://www.python.org/downloads/)

Make sure pip is installed by running `python -m pip --version` or `pip --version`
* [Install pip](https://pip.pypa.io/en/stable/installation/) if it's not installed

Clone or download this repository and open the folder in your terminal
* Ask for help if you're confused on how to do this!

In the repository folder, run `pip install -r requirements.txt`

Now, you can get started writing code! Open client/competitor.py for an example bot.

# Running your code

In the repository folder, run `python client/client.py`
