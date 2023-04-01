import asyncio
import websockets
import json
from player import Player, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING
from game import TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN

players = dict()

async def respond(websocket, event, success):
    await websocket.send(json.dumps({"type": event["type"], "success": success}))

async def process_create_invite(player, event):
    opponent = players[event["opponent"]]
    await opponent.websocket.send(json.dumps({"type": "send_invite", "user": player.username}))
    player.invite(opponent)

async def process_invite_response(player, websocket, event):
    if event["accept"]: 
        player.accept_game()
        game = player.game
        await websocket.send(
            json.dumps({"type": "game_update", "p1": game.p1_bots, "p2": game.p2_bots, "errors": []}))
        await player.opponent.websocket.send(
            json.dumps({"type": "game_update", "p1": game.p1_bots, "p2": game.p2_bots, "errors": []}))
    else: player.deny_game()

async def submit_turn(player, websocket, event):
    game = player.game
    p1_errors, p2_errors = game.submit_turn(player.player_num, event["actions"])
    if game.status == TURN_OVER:
        if player.player_num == 1:
            player_errors = p1_errors
            opponent_errors = p2_errors
        else:
            player_errors = p2_errors
            opponent_errors = p1_errors
        await websocket.send(
            json.dumps({"type": "game_update", "p1": game.p1_bots, "p2": game.p2_bots, "errors": player_errors}))
        await player.opponent.websocket.send(
            json.dumps({"type": "game_update", "p1": game.p1_bots, "p2": game.p2_bots, "errors": opponent_errors}))

async def handle_player(player):
    websocket, username = player.websocket, player.username
    print("Logged in", username)

    async for message in websocket:
        try:
            event = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"type": "invalid_request"}))
            continue
        
        if event["type"] == "create_invite":
            #Check if given opponent exists and does not already have an invite
            if event["opponent"] in players and event["opponent"] != username and players[event["opponent"]].status == WAITING:
                await respond(websocket, event, True)
                await process_create_invite(player, event)
            else: await respond(websocket, event, False)
        
        elif event["type"] == "invite_response":
            #Check if the player has an invite to respond to
            if player.status == RECEIVED_INVITE:
                await respond(websocket, event, True)
                await process_invite_response(player, websocket, event)
            else: await respond(websocket, event, False)

        elif event["type"] == "turn":
            if player.status == PLAYING:
                await respond(websocket, event, True)
                await submit_turn(player, websocket, event)
            else: await respond(websocket, event, False)

async def handler(websocket):
    player = None
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

    try:
        await handle_player(player)
    finally:
        del players[username]

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever

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
    "p1": [[bot 1 health, bot 1 ammo], [bot 2 health, bot 2 ammo]...]
    "p2": [[bot 1 health, bot 1 ammo], [bot 2 health, bot 2 ammo]...]
    "errors": [[error code, bot number], [error code, bot number]...]
}
'''