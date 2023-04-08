from game import Game

#Player status constants
WAITING, PLAYING = 0, 1

class GameController:
    """
    Representation:
    player1: Player
    player2: Player

    Functions:
    constructor: initializes a game between two websocket connections (players); assumes no games are in progress between the two players right now
    play_game(): plays a full game between two players; throws exceptions if something bad happens (e.g. player disconnect or timeout); returns winner of game
    """
    
    def __init__(self, player1, player2):
        """
        Initializes a game between two players.
        
        """
        self.player1 = player1 
        self.player2 = player2


    async def play_game(self):
        """
        Runs a full game between players
        
        Preconditions: player1 and player2 are not currently in a game
        Throws: an exception if a player disconnects or times out
        Returns: the username of the winner of the game, or None if it was a tie
        """
        if self.player1.get_status() != WAITING or self.player2.get_status() != WAITING:
            raise TypeError("Expected players to not be in a game") 


class Player:
    def __init__(self, websocket, username):
        self.websocket = websocket
        self.username = username
        self.status = WAITING
        # self.opponent = None
        # self.game = None
        # self.player_num = 0
    
    # def invite(self, opponent):
    #     if self.opponent != None:
    #         self.opponent.status = WAITING
    #         self.opponent.opponent = None
    #     self.status = SENT_INVITE
    #     self.opponent = opponent
    #     opponent.status = RECEIVED_INVITE
    #     opponent.opponent = self

    # def accept_game(self,):
    #     assert self.opponent != None
    #     game = Game()
    #     self.game = game
    #     self.status = PLAYING
    #     self.player_num = 1
    #     self.opponent.game = game
    #     self.opponent.status = PLAYING
    #     self.opponent.player_num = 2

    # def deny_game(self):
    #     assert self.opponent != None
    #     self.status = WAITING
    #     self.opponent.status = WAITING
    #     self.opponent.opponent = None
    #     self.opponent = None

    # def reset(self):
    #     if self.opponent != None:
    #         self.opponent.status = WAITING
    #         self.opponent.opponent = None
    #         self.opponent.game = None
    #         self.opponent.player_num = 0
    #     self.status = WAITING
    #     self.opponent = None
    #     self.game = None
    #     self.player_num = 0
