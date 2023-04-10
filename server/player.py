from game import Game, P1_WIN, P2_WIN, TIE
import json
import websockets
import asyncio
import uuid

#Player status constants
WAITING, PLAYING = 0, 1

class PlayerAlreadyInGameError(TypeError):
    """
    Represents if a game was requested between two players while one of the players was already in a game
    """
    pass

class PlayerDisconnectError(RuntimeError):
    """
    Represents a player error (disconnect)
    """
    pass

class PlayerTimeoutError(RuntimeError):
    """
    Represents a player timing out error 
    """
    pass

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
    
    def __init__(self, player1, player2):
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
        self.error = None
        self.id = uuid.uuid4()

    def get_id(self):
        """
        returns a id unique to this game
        """
        return self.id

    async def play_game(self):
        """
        Runs a full game between players.
        
        Preconditions: player1 and player2 are not currently in a game
        Throws: 
            a PlayerDisconnectError if a player disconnects
            a PlayerTimeoutError if a player times out
            a PlayerAlreadyInGameError if a player was already in the game
        Returns: the username of the winner of the game, or None if it was a tie
        """
        if (self.player1.username < self.player2.username):
            asyncio.acquire(self.player1.username)
            asyncio.acquire(self.player2.username)
        else:
            asyncio.acquire(self.player2.username)
            asyncio.acquire(self.player1.username)

        if self.player1.status != WAITING or self.player2.status != WAITING:
            raise TypeError("Expected players to not be in a game")  
        while self.game.status not in (P1_WIN, P2_WIN, TIE):
            try:
                self.step_turn()
            except Exception as e:
                self.error = e
                raise e
    
    async def step_turn(self):
        """
        Steps a single turn of a game between two players
        """
        player1_msg = json.dumps({
            "type": "game_update", 
            "bots": self.game.p1_bots, 
            "op_bots": self.game.p2_bots, 
            "errors": self.game.p1_errors
        })
        player2_msg = json.dumps({
            "type": "game_update", 
            "bots": self.game.p2_bots, 
            "op_bots": self.game.p1_bots, 
            "errors": self.game.p2_errors
        })
        # [[p1 actions ], []]
        actions = await asyncio.gather(
                self.player1.do_turn_request(self, player1_msg),
                self.player2.do_turn_request(self, player2_msg)
            )
        self.game.submit_turn(self, *actions)
        self.history.append(json.dumps({
            'game_state': self.game.dumps(), 
            'actions': actions
        }))

    def get_result(self):
        """
        Returns some summarized game result 
        TODO: clarify what return values are
        """
        return json.dumps({
            'history': self.history,
            'errored': self.error is not None
        })

class Player:
    def __init__(self, websocket, username):
        self.websocket = websocket
        self.username = username
        self.status = WAITING
        self.lock = asyncio.Lock()
        # self.opponent = None
        # self.game = None
        # self.player_num = 0
    
    async def do_turn_request(self, turn_message):
        """
        Notify the player that they should play a turn, and waits for the result
        of the player's turn.

        Returns the actions that the player requested for their turn

        Throws an exception if a player disconnects or times out
        """
        # TODO: lock on game?
        try:
            await self.websocket.send(turn_message)
        except:
            raise PlayerDisconnectError()
        try:
            response = await asyncio.wait_for(self.websocket.recv(), 1)
            if (response['type'] == 'turn'):
                return response['actions']
        except:
            raise PlayerTimeoutError()
        
    # async def is_connected(self):
    #     try:
    #         await asyncio.wait_for(self.websocket.ping(), 1)
    #     except:
    #         return False
    #     return True
        
    async def send_game_over(self, winner_username):
        pass