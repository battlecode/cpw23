from game import Game, P1_WIN, P2_WIN, TIE
import json
import jsonschema
import websockets
from websockets.exceptions import ConnectionClosed
import asyncio
import uuid

MAX_MESSAGE_SIZE = 2000

class Player:
    def __init__(self, websocket, username):
        self.websocket = websocket
        self.username = username
        self.lock = asyncio.Lock()
    
    async def send_message(self, message):
        await self.websocket.send(message)

    async def send_begin_message(self, game_id, bots, op_bots, op_name):
        print('sent begin msg to ', self.username)
        await self.websocket.send(json.dumps({
            "type": "begin_game",
            "game_id": game_id,
            "op_name": op_name,
            "bots": bots,
            "op_bots": op_bots,
            "errors": [-1 for i in range(len(bots))], 
            "op_actions": [{"type":"none"} for i in range(len(bots))]
        }))
    
    async def send_game_update(self, game_id, turn, bots, op_bots, actions, op_actions, action_errors):
        print('turn', turn, 'sent game update to', self.username, 
        'with value', bots, op_bots, action_errors)
        await self.websocket.send(json.dumps({
            "type": "game_update",
            "game_id": game_id,
            "turn": turn,
            "bots": bots,
            "op_bots": op_bots,
            "actions": actions,
            "op_actions": op_actions,
            "errors": action_errors
        }))

    async def send_game_over(self, game_id, winner, errors, history):
        """
        Send a game over message to the player. Does not throw 
        an exception if the send fails. 
        """
        try:
            print('sending game over', winner, errors)
            await self.websocket.send(json.dumps({
                "type": "game_over",
                "game_id": game_id,
                "winner": winner,
                "errors": errors,
                "history": history
            }))
        except:
            pass

    async def wait_for_player_turn(self, game_id, timeout):
        """
        Waits for a player to send their turn actions. 
        
        `timeout` is the time to wait for in seconds.

        Returns the list of actions requested by the player

        Raises a TimeoutError if the turn message is not received by the timeout
        Raises a ConnectionClosed error if the websocket is closed
        """
        async def receive_helper():
            player_actions = None
            while player_actions is None:
                response = await self.websocket.recv()
                player_actions = self.parse_turn_message(game_id, response)
                if player_actions is None:
                    await self.send_invalid_message()
            return player_actions

        return await asyncio.wait_for(receive_helper(), timeout)
    
    def parse_turn_message(self, game_id, turn_message):
        """
        Returns a list of actions for this player, or None if the input is invalid.
        turn_message is expected to be a json string as described in server.py7
        """
        if len(turn_message) > MAX_MESSAGE_SIZE:
            # ignore overly large json responses
            return None
        try:
            result = json.loads(turn_message)
            try:
                jsonschema.validate(result, SUBMIT_TURN_SCHEMA)
            except Exception as e:
                print(e)
            if ('type' in result and 'actions' in result
                and result['type'] == 'turn' and 
                result['game_id'] == game_id):
                return result['actions']
        except:
            return None
    
    async def send_invalid_message(self):
        """
        Send a message to the player that their request was invalid.
        """
        await self.websocket.send(json.dumps({ "type": "invalid_request" }))

class GameController:
    """
    Representation:
    player1: Player
    player2: Player
    id: number (id of the game)

    Functions:
    constructor: initializes a game between two websocket connections (players); 
    play_game(): plays a full game between two players; throws exceptions if something bad happens (e.g. player disconnect or timeout); returns winner of game
                    assumes no games are in progress between the two players right now
    """
    
    def __init__(self, player1: Player, player2: Player):
        """
        Initializes a game between two players.
        """
        self.player1 = player1 
        self.player2 = player2
        self.game = Game()
        # records gamestate and actions taken resulting in the gamestate
        self.history = [json.dumps({
            'game_state': self.game.dumps(),
            'actions': None,
        })]

        self.game_ended = False

        self.winner = None
        self.errored_players = None

        self.id = str(uuid.uuid4())

    def get_id(self):
        """
        Returns a id unique to this game
        """
        return self.id

    def is_game_over(self):
        """
        Returns if the game has ended or not (whether from player disconnect, 
        timeout, or game tie/win)
        """
        return self.game_ended

    def get_results(self):
        """
        Returns: 
        If the game is over, returns a tuple of length 2. The first element is 
        the username of the winner, or None if it was a tie. The second element 
        is a tuple containing the username(s) of player(s) that errored during 
        the game.
        If the game is not over, return None
        """
        if self.game_ended:
            return self.winner, self.errored_players
        return None

    async def play_game(self):
        """
        Runs a full game between players. Waits for the games that players are currently in
        to end before playing the game. 

        If a player disconnects or times out during the game, they automatically lose. 
        If both players disconnect/time out or any one times out before the game, there is a tie.
        """
        print('playing game')
        # acquire player locks in order
        # ensures that a player is only in one game at once
        if (self.player1.username < self.player2.username):
            await self.player1.lock.acquire()
            await self.player2.lock.acquire()
        else:
            await self.player2.lock.acquire()
            await self.player1.lock.acquire()
        
        try:
            # send game begin messages to each player
            try:
                await self.player1.send_begin_message(
                    self.id, self.game.p1_bots, self.game.p2_bots, self.player2.username
                )
            except:
                print('begin error', self.player1.username)
                self.errored_players = (self.player1.username,)
                return
            try:
                await self.player2.send_begin_message(
                    self.id, self.game.p2_bots, self.game.p1_bots, self.player1.username
                )
            except:
                print('begin error', self.player2.username)
                self.errored_players = (self.player2.username,)
                # if player 2 errors but player 1 didn't error, we tell player 1
                # that the game is over
                await self.player1.send_game_over(self.get_id(), None, self.errored_players, self.history)
                return
            
            # run the game
            while not self.game.is_game_over():
                errors = await self.step_turn()
                if len(errors) > 0:
                    self.errored_players = errors
                    if len(errors) == 1 and errors[0] == self.player1.username: 
                        # player 1 errored, so player 2 wins
                        self.winner = self.player2.username
                    elif len(errors) == 1: 
                        # player 2 errored, so player 1 wins
                        self.winner = self.player1.username
                    # if len(errors) then it's a tie b/c both errored
                    break
            
            winner_code = self.game.get_winner()
            if winner_code == P1_WIN:
                self.winner = self.player1.username
            elif winner_code == P2_WIN:
                self.winner = self.player2.username
            
            # send game end messages to each player
            await self.player1.send_game_over(self.get_id(), self.winner, self.errored_players, self.history)
            await self.player2.send_game_over(self.get_id(), self.winner, self.errored_players, self.history)
        except Exception as e:
            print(f'error in game {self.get_id()}, {e}')
        finally:
            self.game_ended = True
            self.player1.lock.release()
            self.player2.lock.release()
    
    async def step_turn(self):
        """
        Steps a single turn of a game between two players. 

        If an error receiving turn data from a player occurs, returns a tuple
        containing the username(s) of the player(s) that errored and does not
        step the turn. If no error occurred, step the turn and return an empty 
        tuple.
        """
        # receive turn actions
        # [[p1 actions], [p2 actions]]
        actions = await asyncio.gather(
                self.player1.wait_for_player_turn(self.id, 3),
                self.player2.wait_for_player_turn(self.id, 3),
                return_exceptions=True)
        errors = ()
        if isinstance(actions[0], Exception):
            errors += (self.player1.username, )
        if isinstance(actions[1], Exception):
            errors += (self.player2.username, )
        if len(errors) > 0:
            return errors
        
        player1_actions, player2_actions = actions

        # update the actual game
        self.game.submit_turn(*actions)
        self.history.append(json.dumps({
            'game_state': self.game.dumps(), 
            'actions': actions
        }))

        # send game updates
        game_updates = await asyncio.gather(
            self.player1.send_game_update(self.id, len(self.history)-1,
                self.game.p1_bots, self.game.p2_bots, player1_actions, player2_actions, self.game.p1_errors),
            self.player2.send_game_update(self.id, len(self.history)-1,
                self.game.p2_bots, self.game.p1_bots, player2_actions, player1_actions, self.game.p2_errors),
            return_exceptions=True
        )
        if isinstance(game_updates[0], Exception):
            errors += (self.player1.username, )
        if isinstance(game_updates[1], Exception):
            errors += (self.player2.username, )
        return errors


# TODO: validation with schema
SUBMIT_TURN_SCHEMA = {
    "type": "object",
    "properties": { 
        "type": {"type": "string"},
        "game_id": {"type": "string"},
        "turn": {"type": "number"},
        "actions": {
            # "actions": [
            #     {"type": "none/load/launch/shield", "target": number, "strength": number},
            #     ...for each bot in order
            # ]
            "type": "array",
            "items": { # validate each item of the actions arr
                "type": "object",
                "properties": {
                    "type": { "type": "string", "pattern": "^none|load|launch|shield$"},
                    "target": { "type": "integer", "minimum": 0, "maximum": 2 },
                    "strength": { 'type': "integer" }
                }
            }
        }    
    }
}
