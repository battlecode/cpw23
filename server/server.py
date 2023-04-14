import asyncio
import websockets
import json
from player import Player, GameController
from autoscrim import autoscrim 
from tournament_runner import run_tourney
import os.path

# current console command
SERVER_MODES = ("autoscrim", "tournament")
server_mode = SERVER_MODES[0]

def check_mode():
    """
    Checks our command line for input, and runs associated code if 
    appropriate. Check README for commands.
    """
    for mode in SERVER_MODES:
        if os.path.isfile(mode):
            change_mode(mode)

def change_mode(mode):
    """
    Given a valid server mode, toggle server to run in that mode.
    """
    # set our file-wide server mode
    global server_mode
    if mode in SERVER_MODES:
        if mode != server_mode:
            print(f"{mode} enabled!")
        server_mode = mode


# a dict mapping player usernames to Player objects
players = dict()

async def respond(websocket, event, success):
    await websocket.send(json.dumps({"type": event["type"], "success": success}))

async def handle_player(player):
    global players
    websocket, username = player.websocket, player.username
    print("Logged in", username)

    # make sure web socket stays connected; ping it every 30 seconds
    while True:
        # TODO: figure out if this ping interferes w/ autoscrim pings
        await websocket.ping()
        await asyncio.sleep(5)

async def handler(websocket):
    global players
    player = None
    # wait for login
    async for message in websocket:
        try:
            event = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"type": "invalid_request"}))
            continue

        if event["type"] == "login":
            username = str(event["user"])
            if username in players:
                await respond(websocket, event, False)
            else:
                player = Player(websocket, username)
                players[username] = player
                await respond(websocket, event, True)
                break
    # then handle player
    try:
        await handle_player(player)
    except Exception as e:
        print(f'{username} disconnected with Exception', e)
    finally:
        if username in players:
            del players[username]

async def main():
    global players
    global server_mode
    async with websockets.serve(handler, "", 8001):
        while True:
            await asyncio.sleep(45)
            # determine which mode we are in, then run appropriate code
            check_mode()
            if server_mode == SERVER_MODES[1]:
                await run_tourney(players)
            # we want to be in autoscrim mode by default
            else:
                await autoscrim(players)

if __name__ == "__main__":
    asyncio.run(main())

'''
Websocket communication

CLIENT -> SERVER

Initial login
{ "type": "login", "user": "your username" }

Submit turn
{
    "type": "turn",
    "game_id": an uuid for the game the turn belongs to ,
    "turn": the turn number of this turn,
    "actions": [
        {"type": "none/load/launch/shield", "target": number, "strength": number},
        ...for each bot in order
    ]
}

SERVER -> CLIENT

Upon client login, send
{ "type": "login", "success": true/false }

When a game begins, send
{
    "type": "begin_game",
    "game_id": an uuid for this game
    "op_name": opponent's username
    "bots": [[bot 1 health, bot 1 ammo, error_code], [bot 2 health, bot 2 ammo, error]...]
    "op_bots": [[bot 1 health, bot 1 ammo], [bot 2 health, bot 2 ammo]...]
    "op_actions": [{"type":"none"} for num_bots]
}

When a turn ends, send game state:
{
    "type": "game_update",
    "game_id": an uuid for this game,
    "turn": the turn number that just occurred,
    "bots": [[bot 1 health, bot 1 ammo, error_code], [bot 2 health, bot 2 ammo, error]...]
    "op_bots": [[bot 1 health, bot 1 ammo], [bot 2 health, bot 2 ammo]...],
    "actions": [{"type": "none/load/launch/shield", "target": number, "strength": number} for each bot in order],
    "op_actions": [{"type": "none/load/launch/shield", "target": number, "strength": number} for each bot in order],
    "errors": [[error code, bot number], [error code, bot number]...]
}

When a game is over, send
{
    "type": "game_over",
    "game_id": uuid for this game,
    "winner": the username of the winner, or null/None if there was a tie,
    'tie': boolean for if there was a tie
    "errors": a list of usernames that disconnected,
    "history": a list containing the history of the game
}

When receiving invalid requests, send
{ "type": "invalid_request" }
'''
