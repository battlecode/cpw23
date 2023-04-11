import asyncio
import websockets
import json
import time
from competitor import Competitor
from controller import Controller
from visualizer import Visualizer

WAITING, RECEIVED_INVITE, PLAYING = 0, 1, 2

status = WAITING
controller = None
visualizer = Visualizer()
competitor = Competitor()

async def play_and_submit_turn(websocket, event, controller, competitor):
    if controller == None: controller = Controller()
    controller.reset()
    controller.player_state = event["bots"]
    controller.opponent_state = event["op_bots"]
    controller.prev_op_actions = event["op_actions"]
    def parse_round_errors(e):
        error_codes = [-1 for _ in range(len(event["op_bots"]))]
        for code, bot in e:
            error_codes[bot] = code
        return error_codes
    controller.prev_round_errors = parse_round_errors(event["errors"])
    competitor.play_turn(controller)
    await websocket.send(json.dumps({"type": "turn", "actions": controller.actions}))

async def consumer(websocket, message):
    #This is sub-optimal, but there is no easy way around it
    global status, controller, competitor
    event = json.loads(message)

    if event["type"] == "send_invite":
        status = RECEIVED_INVITE
        print(event["user"], "has invited you. Enter y/n to respond.")
    elif event["type"] == "game_update":
        print(message)
        status = PLAYING
        await play_and_submit_turn(websocket, event, controller, competitor)
    elif event["type"] == "game_over":
        status = WAITING
        print("Game over. Outcome:", event["outcome"])
    else: 
        status = WAITING

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
    await websocket.send(json.dumps({"type": "login", "user": str(time.time())}))

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
    def execute():
        asyncio.run(main())
    visualizer.run(execute)
