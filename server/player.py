from game import Game

#Player status constants
WAITING, SENT_INVITE, RECEIVED_INVITE, PLAYING = 0, 1, 2, 3

class Player:
    
    def __init__(self, websocket, username):
        self.websocket = websocket
        self.username = username
        self.status = WAITING
        self.opponent = None
        self.game = None

    def invite(self, opponent):
        if self.opponent != None:
            self.opponent.status = WAITING
            self.opponent.opponent = None
        self.status = SENT_INVITE
        self.opponent = opponent
        opponent.status = RECEIVED_INVITE
        opponent.opponent = self

    def accept_game(self,):
        assert self.opponent != None
        game = Game()
        self.game = game
        self.status = PLAYING
        self.opponent.game = game
        self.opponent.status = PLAYING

    def deny_game(self):
        assert self.opponent != None
        self.status = WAITING
        self.opponent.status = WAITING
        self.opponent.opponent = None
        self.opponent = None
