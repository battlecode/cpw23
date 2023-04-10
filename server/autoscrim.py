import asyncio
import websockets
import json
from player import Player, PlayerDisconnectError, PlayerTimeoutError, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING
from game import TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN, TIE
import random
import time
from server import GameController

async def autoscrim(players):
    """
    Runs autoscrims between all the players passed in.

    Arguments:
    players: a dictionary mapping player usernames (strings) to Player objects
    """
    num_players = len(players)
    # number of games (ignoring one player if there are an odd # of players)
    num_games = num_players // 2
    is_even = num_players % 2 == 0

    shuffled = list(players.values())
    random.shuffle(shuffled)

    player_set_1 = shuffled[:num_games]
    player_set_2 = shuffled[num_games:]

    games = [pair for pair in zip(player_set_1, player_set_2)]

    # if odd, match the extra player with the first player in player_arr_1
    if not is_even:
        # extra player is located at player_set_2[-1]
        games.append((player_set_1[0], player_set_2[-1]))

    games_to_run = [game_wrapper(pair) for pair in games]
    await asyncio.gather(*games_to_run)
    

async def game_wrapper(pair):
    p1, p2 = pair
    # try running a game twice before giving up
    for i in range(2):
        try:
            game = GameController(p1, p2)
            game.play_game()
            break
        except PlayerTimeoutError:
            # wait 5 seconds before trying again
            asyncio.sleep(5)
        except PlayerDisconnectError:
            break