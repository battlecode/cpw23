import asyncio
import websockets
import json
from player import Player, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING
from game import TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN, TIE
import random
import time
from server import GameController

def autoscrim(players):
    # handle odd number of players pls 
    num_players = len(players) // 2
    player_set_1, player_set_2 = (players[:num_players], players[num_players:])

    random.shuffle(player_set_1)
    random.shuffle(player_set_2)

    games = []
    for pair in zip(player_set_1, player_set_2):
        games.append(GameController(*pair))

    # create async loop
    loop = asyncio.get_event_loop()
    games_to_run = [loop.create_task(game_wrapper(game)) for game in games]
    loop.run_until_complete(asyncio.gather(*games_to_run))
    

def game_wrapper(game):
    try:
        game.play_game()

    except PlayerTimeoutError:
        time.sleep(0.01)
        try:
            game.play_game()
        except (PlayerDisconnectError, PlayerTimeoutError):
            pass #
    finally: 
        return