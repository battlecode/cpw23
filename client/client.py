import asyncio
import websockets
import json
import time
import copy
from competitor import Competitor
from controller import Controller
from visualizer import Visualizer

WAITING, PLAYING = 0, 1
ENABLE_PRINT = False

status = WAITING
game_id = None
competitor = None
username = str(time.time())
op_username = ""
game_history = []
visualizer = Visualizer()
last_actions = []

async def begin_game(websocket, event):
    if ENABLE_PRINT:
        print('received begin message', event)
    global game_id, competitor, op_username
    game_id = event['game_id']
    competitor = Competitor()
    op_username = event['op_name']
    await play_and_submit_turn(websocket, game_id, 0, event['bots'], event['op_bots'], event['op_actions'], event['errors'], competitor)

async def play_and_submit_turn(websocket, game_id, turn, my_bots, op_bots, op_actions, errors, competitor):
    global last_actions
    controller = Controller(turn, my_bots, op_bots, op_actions, errors)
    competitor.play_turn(controller)
    if ENABLE_PRINT:
        print('submitting turn', controller.actions)
    await websocket.send(json.dumps({
        "type": "turn", 
        'game_id': game_id, 
        'turn': turn,
        "actions": controller.actions}))
    last_actions = copy.deepcopy(controller.actions)

async def consumer(websocket, message):
    #This is sub-optimal, but there is no easy way around it
    global status, competitor, game_id
    event = json.loads(message)

    if event["type"] == "login" and not event['success']:
        websocket.close()
        if ENABLE_PRINT:
            print(f'The username "{username}" is already in use. Please use a different username.')
    elif event['type'] == 'begin_game':
        if ENABLE_PRINT:
            print('beginning game', event)
        visualizer.render_game(event, "begin")
        await begin_game(websocket, event)
    elif event["type"] == "game_update" and event['game_id'] == game_id:
        if ENABLE_PRINT:
            print('game update', event)
        visualizer.render_game(
            event | {"actions": copy.deepcopy(last_actions), "name": username, "op_name": op_username},
            "update"
        )
        status = PLAYING
        def parse_round_errors(e):
            error_codes = [-1 for _ in range(len(event["op_bots"]))]
            for code, bot in e:
                error_codes[bot] = code
            return error_codes
        await play_and_submit_turn(websocket, game_id, event['turn'], event['bots'], event['op_bots'], event['op_actions'], 
                                   parse_round_errors(event["errors"]), competitor)
    elif event["type"] == "game_over" and event['game_id'] == game_id:
        game_id = None
        game_history.append(event)
        status = WAITING
        if ENABLE_PRINT:
            print(f"Game over. Winner: {event['winner']}, Errors: {event['errors']}")
        visualizer.render_game(event, "end")
    else: 
        status = WAITING

async def consumer_handler(websocket):
    async for message in websocket:
        await consumer(websocket, message)

async def handler(websocket):
    #TODO for testing, set player username to the current time so that we don't have to make another copy of competitior script
    await websocket.send(json.dumps({"type": "login", "user": username}))

    consumer_task = asyncio.create_task(consumer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

async def main():
    uri = "ws://cpw.battlecode.org:8001/"
    async with websockets.connect(uri, ssl=None) as websocket:
        await handler(websocket)

if __name__ == "__main__":
    def execute():
        asyncio.run(main())
    visualizer.run(execute)
