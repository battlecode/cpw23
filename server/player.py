from game import Game, P1_WIN, P2_WIN, TIE
import json
import jsonschema
import websockets
from websockets.exceptions import ConnectionClosed
import asyncio
import uuid

class PlayerAlreadyInGameError(TypeError):
    """
    Represents if a game was requested between two players while one of the players was already in a game
    """
    pass

class PlayerDisconnectError(ConnectionClosed):
    """
    Represents a player error (disconnect)
    """
    pass

class PlayerTimeoutError(RuntimeError):
    """
    Represents a player timing out error 
    """
    pass

MAX_MESSAGE_SIZE = 2000

class Player:
    def __init__(self, websocket, username):
        self.websocket = websocket
        self.username = username
        self.lock = asyncio.Lock()
    
    async def send_message(self, message):
        await self.websocket.send(message)

    async def send_begin_message(self, game_id, bots, op_bots):
        print('sent begin msg to ', self.username)
        await self.websocket.send(json.dumps({
            "type": "begin_game",
            "game_id": game_id,
            "bots": bots,
            "op_bots": op_bots
        }))
    
    async def send_game_update(self, game_id, turn, bots, op_bots, action_errors):
        print('turn', turn, 'sent game update to', self.username, 
        'with value', bots, op_bots, action_errors)
        await self.websocket.send(json.dumps({
            "type": "game_update",
            "game_id": game_id,
            "turn": turn,
            "bots": bots,
            "op_bots": op_bots,
            "action_errors": action_errors
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

    async def wait_for_player_turn(self, timeout):
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
                player_actions = self.parse_turn_message(response)
                if player_actions is None:
                    await self.send_invalid_message()
            return player_actions

        return await asyncio.wait_for(receive_helper(), timeout)
    
    def parse_turn_message(self, turn_message):
        """
        Returns a list of actions for this player, or None if the input is invalid.
        turn_message is expected to be a json string as described in server.py7
        """
        # TODO here: implement validation with jsonschema
        if len(turn_message) > MAX_MESSAGE_SIZE:
            # ignore overly large json responses
            return None
        try:
            result = json.loads(turn_message)
            if ('type' in result and 'actions' in result
                and result['type'] == 'turn'):
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

        self.winner = None
        self.player_errors = None

        self.id = str(uuid.uuid4())

    def get_id(self):
        """
        Returns a id unique to this game
        """
        return self.id

    def get_results(self):
        """
        Returns: 
        If the game is over, returns a tuple of length 2. The first element is 
        the username of the winner, or None if it was a tie. The second element 
        is a tuple containing the username(s) of player(s) that errored during 
        the game.
        If the game is not over, return None
        """
        if self.game.is_game_over():
            return self.winner, self.player_errors
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
                    self.id, self.game.p1_bots, self.game.p2_bots)
            except:
                print('begin error', self.player1.username)
                self.player_errors = (self.player1.username,)
                return
            try:
                await self.player2.send_begin_message(
                    self.id, self.game.p2_bots, self.game.p1_bots
                )
            except:
                print('begin error', self.player2.username)
                self.player_errors = (self.player2.username,)
                # if player 2 errors but player 1 didn't error, we tell player 1
                # that the game is over
                await self.player1.send_game_over(self.get_id(), None, self.player_errors, self.history)
                return
            
            # run the game
            while not self.game.is_game_over():
                errors = await self.step_turn()
                if len(errors) > 0:
                    self.player_errors = errors
                    if len(errors) == 1 and errors[0] == self.player1.username: # player 1 errored
                        self.winner = self.player2.username
                    elif len(errors) == 1: # player 2 errorred
                        self.winner = self.player1.username
                    break
            
            winner_code = self.game.get_winner()
            if winner_code == P1_WIN:
                self.winner = self.player1.username
            elif winner_code == P2_WIN:
                self.winner = self.player2.username
            
            # send game end messages to each player
            await self.player1.send_game_over(self.get_id(), self.winner, self.player_errors, self.history)
            await self.player2.send_game_over(self.get_id(), self.winner, self.player_errors, self.history)
        finally:
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
                self.player1.wait_for_player_turn(2),
                self.player2.wait_for_player_turn(2),
                return_exceptions=True)
        errors = ()
        if isinstance(actions[0], Exception):
            errors += (self.player1.username, )
        if isinstance(actions[1], Exception):
            errors += (self.player2.username, )
        if len(errors) > 0:
            return errors

        # update the actual game
        self.game.submit_turn(*actions)
        self.history.append(json.dumps({
            'game_state': self.game.dumps(), 
            'actions': actions
        }))

        # send game updates
        game_updates = await asyncio.gather(
            self.player1.send_game_update(self.id, len(self.history)-1,
                self.game.p1_bots, self.game.p2_bots, self.game.p1_errors),
            self.player2.send_game_update(self.id, len(self.history)-1,
                self.game.p2_bots, self.game.p1_bots, self.game.p2_errors),
            return_exceptions=True
        )
        if isinstance(game_updates[0], Exception):
            errors += (self.player1.username, )
        if isinstance(game_updates[1], Exception):
            errors += (self.player2.username, )
        return errors