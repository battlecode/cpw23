import asyncio
import websockets
import json
from player import Player, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING

players = dict()

async def respond(websocket, event, success):
    await websocket.send(json.dumps({"type": event["type"], "success": success}))

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
            if event["opponent"] in players and players[event["opponent"]].status == WAITING:
                opponent = players[event["opponent"]]
                await respond(websocket, event, True)
                await opponent.websocket.send(json.dumps({"type": "send_invite", "user": username}))
                player.invite(opponent)
            else: await respond(websocket, event, False)
        
        elif event["type"] == "invite_response":
            #Check if the player has an invite to respond to
            if player.status == RECEIVED_INVITE:
                await respond(websocket, event, True)
                if event["accept"]: 
                    player.accept_game()
                    await websocket.send(json.dumps({"type": "start_game"}))
                    await player.opponent.websocket.send(json.dumps({"type": "start_game"}))
                else: player.deny_game()
            else: await respond(websocket, event, False)

        elif event["type"] == "turn":
            if player.status == PLAYING:
                await respond(websocket, event, True)
                await respond(player.opponent.websocket, event, False)
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