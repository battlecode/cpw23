import asyncio
import websockets
import json
import time

received_invite = False

async def consumer(message):
    #This is sub-optimal, but there is no easy way around it
    global received_invite
    event = json.loads(message)
    if event["type"] == "send_invite":
        received_invite = True
        print(event["user"], "has invited you. Enter y/n to respond.")
    else: 
        received_invite = False
        print(message)

async def producer():
    while True:
        command = await asyncio.get_event_loop().run_in_executor(None, lambda: input().split())
        if received_invite:
            return json.dumps({"type": "invite_response", "accept": command[0].lower() == 'y'})
        elif command[0] == "invite":
            return json.dumps({"type": "create_invite", "opponent": command[1]})

async def consumer_handler(websocket):
    async for message in websocket:
        await consumer(message)

async def producer_handler(websocket):
    while True:
        message = await producer()
        await websocket.send(message)

async def handler(websocket):
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
    asyncio.run(main())