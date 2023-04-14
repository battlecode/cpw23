import asyncio
import websockets
import json
import time
import copy
import traceback
from competitor import Competitor
from controller import Controller
from visualizer import Visualizer

WAITING, PLAYING = 0, 1
ENABLE_PRINT = False

status = WAITING
game_id = None
competitor = None
op_username = ""
game_history = []
visualizer = Visualizer()
exceptions = ""

async def cleanup(websocket):
    websocket.close()

async def begin_game(websocket, event):
    if ENABLE_PRINT:
        print('received begin message', event)
    global game_id, competitor, op_username
    game_id = event['game_id']
    competitor = Competitor()
    op_username = event['op_name']
    await play_and_submit_turn(websocket, game_id, 0, event['bots'], event['op_bots'], event['op_actions'], event['errors'], competitor)

async def play_and_submit_turn(websocket, game_id, turn, my_bots, op_bots, op_actions, errors, competitor):
    global exceptions
    controller = Controller(turn, my_bots, op_bots, op_actions, errors)
    try:
        competitor.play_turn(controller)
        exceptions = ""
    except Exception:
        exceptions = traceback.format_exc().replace("\n", " ")

    if ENABLE_PRINT:
        print('submitting turn', controller.actions)
    await websocket.send(json.dumps({
        "type": "turn", 
        'game_id': game_id, 
        'turn': turn,
        "actions": controller.actions}))

async def consumer(websocket, message):
    #This is sub-optimal, but there is no easy way around it
    global status, competitor, game_id
    event = json.loads(message)

    if event["type"] == "login" and not event['success']:
        visualizer.render_error(f'The username "{Competitor.username}" is already in use. Please quit and use a different username.')
        await cleanup(websocket)
    elif event['type'] == 'begin_game':
        if ENABLE_PRINT:
            print('beginning game', event)
        visualizer.render_game(event, "begin")
        await begin_game(websocket, event)
    elif event["type"] == "game_update" and event['game_id'] == game_id:
        if ENABLE_PRINT:
            print('game update', event)
        visualizer.render_game(
            event | { "name": Competitor.username, "op_name": op_username, "exceptions": exceptions},
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
    await websocket.send(json.dumps({"type": "login", "user": Competitor.username}))

    consumer_task = asyncio.create_task(consumer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

async def main():
    uri = "ws://cpw.battlecode.org:8001/"
    #uri = "ws://localhost:8001/"
    async with websockets.connect(uri, ssl=None) as websocket:
        await handler(websocket)

if __name__ == "__main__":
    def execute():
        asyncio.run(main())
    visualizer.run(execute)
