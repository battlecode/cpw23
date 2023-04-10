import asyncio
import websockets
import json
import time
from competitor import Competitor
from controller import Controller

WAITING, PLAYING = 0, 1

status = WAITING
game_id = None
competitor = None
username = str(time.time())
game_history = []

async def begin_game(websocket, event):
    global game_id, competitor
    game_id = event['game_id']
    competitor = Competitor()
    play_and_submit_turn(websocket, 0, event['bots'], event['op_bots'], competitor)

async def play_and_submit_turn(websocket, turn, my_bots, op_bots, competitor):
    controller = Controller(turn, my_bots, op_bots)
    competitor.play_turn(controller)
    await websocket.send(json.dumps({"type": "turn", "actions": controller.actions}))

async def consumer(websocket, message):
    #This is sub-optimal, but there is no easy way around it
    global status, competitor
    event = json.loads(message)

    if event["type"] == "login" and not event['success']:
        websocket.close()
        print(f'The username "{username}" is already in use. Please use a different username.')
    elif event['type'] == 'begin_game':
        print('beginning game', event)
        begin_game(websocket, event)
    elif event["type"] == "game_update" and event['game_id'] == game_id:
        print('game update', event)
        status = PLAYING
        await play_and_submit_turn(websocket, event, competitor)
    elif event["type"] == "game_over" and event['game_id'] == game_id:
        game_id = None
        game_history.append(event)
        status = WAITING
        print("Game over. Outcome:", event)
    else: 
        status = WAITING
        print(message)

async def producer():
    while True:
        command = await asyncio.get_event_loop().run_in_executor(None, lambda: input().split())
        if status == RECEIVED_INVITE:
            return json.dumps({"type": "invite_response", "accept": command[0].lower() == 'y'})
        elif command[0] == "invite":
            return json.dumps({"type": "create_invite", "opponent": command[1]})

async def consumer_handler(websocket):
    async for message in websocket:
        await consumer(websocket, message)

async def producer_handler(websocket):
    while True:
        message = await producer()
        await websocket.send(message)

async def handler(websocket):
    #TODO for testing, set player username to the current time so that we don't have to make another copy of competitior script
    await websocket.send(json.dumps({"type": "login", "user": username}))

    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

async def main():
    uri = "ws://localhost:8001/"
    async with websockets.connect(uri, ssl=None) as websocket:
        await handler(websocket)

if __name__ == "__main__":
    asyncio.run(main())