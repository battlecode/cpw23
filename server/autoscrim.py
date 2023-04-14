import asyncio
import websockets
import json
from player import GameController
import random
import time

async def autoscrim(players):
    """
    Runs autoscrims between all the players passed in.
    Arguments:
    players: a dictionary mapping player usernames (strings) to Player objects
    """
    if len(players) < 2:
        print('not enough players to do autoscrims', len(players))
        return

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

    games_results = [game_wrapper(pair) for pair in games]
    print("games to be played:", games)
    await asyncio.gather(*games_results)
    print('finished running all games', games_results)
    

async def game_wrapper(pair):
    p1, p2 = pair
    try:
        game = GameController(p1, p2)
        await game.play_game()
        return game.get_results()
    except Exception as e:
        print('error with ', p1, p2)