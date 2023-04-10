import asyncio
import websockets
import json
from player import Player, PlayerDisconnectError, PlayerTimeoutError, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING
from game import TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN, TIE
import random
import time
from server import GameController

async def autoscrim(players):
    
    num_players = len(players) // 2
    is_even = (len(players) % 2 == 0)

    player_set_1, player_set_2 = (players[:num_players], players[num_players:])

    random.shuffle(player_set_1)
    random.shuffle(player_set_2)

    games = []
    for pair in zip(player_set_1, player_set_2):
        games.append(GameController(*pair))

    # if odd match the last player in player_set_2 with a random player from 1
    if not is_even:
        player = random.choice(player_set_1)
        games.append(GameController(player, player_set_2[-1]))

    games_to_run = [game_wrapper(game) for game in games]
    await asyncio.gather(*games_to_run)
    

async def game_wrapper(game):
    p1, p2 = (game.player1, game.player2)
    try:
        game.play_game()

    except PlayerTimeoutError:
        time.sleep(0.01)
        try:
            new_game = GameController(p1, p2)
            new_game.play_game()
        except (PlayerDisconnectError, PlayerTimeoutError):
            pass