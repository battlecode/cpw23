import asyncio
import websockets
import json
from player import Player, WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING

players = dict()

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
            if event["opponent"] in players:
                opponent = players[event["opponent"]]
                await websocket.send(json.dumps({"type": "create_invite", "success": True}))
                await opponent.websocket.send(json.dumps({"type": "send_invite", "user": username}))
                player.invite(opponent)
            else: await websocket.send(json.dumps({"type": "create_invite", "success": False}))
        
        elif event["type"] == "invite_response":
            if player.status == RECEIVED_INVITE:
                if event["accept"]: 
                    player.accept_game()
                    await websocket.send(json.dumps({"type": "start_game"}))
                    await player.opponent.websocket.send(json.dumps({"type": "start_game"}))
                else: player.deny_game()

        elif event["type"] == "turn":
            if player.status == PLAYING:
                await websocket.send(json.dumps({"type": "turn", "success": True}))
                await player.opponent.websocket.send(json.dumps({"type": "turn", "success": True}))

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
                await websocket.send(json.dumps({"type": "login", "success": False}))
            else:
                player = Player(websocket, username)
                players[username] = player
                await websocket.send(json.dumps({"type": "login", "success": True}))
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