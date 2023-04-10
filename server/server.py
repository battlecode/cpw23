import asyncio
import websockets
import json
from player import Player, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING
from autoscrim import autoscrim 
from game import TURN_OVER, P1_WIN, P2_WIN, TIE

# a dict mapping player usernames to Player objects
players = dict()

async def respond(websocket, event, success):
    await websocket.send(json.dumps({"type": event["type"], "success": success}))

async def submit_turn(player, websocket, event):
    game = player.game
    p1_errors, p2_errors = game.submit_turn(player.player_num, event["actions"])
    if game.status == TURN_OVER:
        if player.player_num == 1:
            player_bots = game.p1_bots
            opponent_bots = game.p2_bots
            player_errors = p1_errors
            opponent_errors = p2_errors
        else:
            player_bots = game.p2_bots
            opponent_bots = game.p1_bots
            player_errors = p2_errors
            opponent_errors = p1_errors
        await websocket.send(
            json.dumps({"type": "game_update", "bots": player_bots, "op_bots": opponent_bots, "errors": player_errors}))
        await player.opponent.websocket.send(
            json.dumps({"type": "game_update", "bots": opponent_bots, "op_bots": player_bots, "errors": opponent_errors}))
    elif game.status == TIE or game.status == P1_WIN or game.status == P2_WIN:
        if game.status == TIE:
            player_outcome = "win"
            opponent_outcome = "win"
        elif game.status == P1_WIN and player.player_num == 1 or game.status == P2_WIN and player.player_num == 2:
            player_outcome = "win"
            opponent_outcome = "loss"
        else:
            player_outcome = "loss"
            opponent_outcome = "win"
        await websocket.send(json.dumps({"type": "game_over", "outcome": player_outcome}))
        await player.opponent.websocket.send(json.dumps({"type": "game_over", "outcome": opponent_outcome}))
        player.reset()


async def handle_player(player):
    websocket, username = player.websocket, player.username
    print("Logged in", username)

    # make sure web socket stays connected; ping it every 30 seconds
    try:
        while True:
            await websocket.ping()
            await asyncio.sleep(30)
    finally:
        del players[username]

    # async for message in websocket:
    #     try:
    #         event = json.loads(message)
    #     except json.JSONDecodeError:
    #         await websocket.send(json.dumps({"type": "invalid_request"}))
    #         continue
        
    #     if event["type"] == "create_invite":
    #         #Check if given opponent exists and does not already have an invite
    #         if event["opponent"] in players and event["opponent"] != username and players[event["opponent"]].status == WAITING:
    #             await respond(websocket, event, True)
    #             await process_create_invite(player, event)
    #         else: await respond(websocket, event, False)
        
    #     elif event["type"] == "invite_response":
    #         #Check if the player has an invite to respond to
    #         if player.status == RECEIVED_INVITE:
    #             await respond(websocket, event, True)
    #             await process_invite_response(player, websocket, event)
    #         else: await respond(websocket, event, False)

    #     elif event["type"] == "turn":
    #         if player.status == PLAYING:
    #             await respond(websocket, event, True)
    #             await submit_turn(player, websocket, event)
    #         else: await respond(websocket, event, False)

async def handler(websocket):
    player = None
    # wait for login
    async for message in websocket:
        try:
            event = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"type": "invalid_request"}))
            continue

        if event["type"] == "login":
            username = event["user"]
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
    finally:
        del players[username]
async def update_players(players):

    players = {username: player for username, player in players.items() if player.is_connected()}

async def main():
    async with websockets.serve(handler, "", 8001):
        while True:
            await asyncio.sleep(60*5)
            autoscrim(players)

if __name__ == "__main__":
    asyncio.run(main())

'''
Websocket communication

CLIENT -> SERVER

Initial login
{"type": "login", "user": "your username"}

Send game invite
{"type": "create_invite", "opponent": "opponent username"}

Respond to game invite
{"type": "invite_response", "accept": true/false}

Submit turn
{
    "type": "turn", 
    "actions": [
        {"type": "none/load/launch/shield", "target": number, "strength": number},
        ...for each bot in order
    ]
}

SERVER -> CLIENT

Initial login
{"type": "login", "success": true/false}

Send game invite
{"type": "create_invite", "success": true/false}

Respond to game invite
{"type": "invite_response", "success": true/false}

Game state (sent when first starting game and after each complete turn)
{
    "type": "game_update",
    "bots": [[bot 1 health, bot 1 ammo, error_code], [bot 2 health, bot 2 ammo, error]...]
    "op_bots": [[bot 1 health, bot 1 ammo], [bot 2 health, bot 2 ammo]...]
    "errors": [[error code, bot number], [error code, bot number]...]
}
'''