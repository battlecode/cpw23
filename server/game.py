
#Gameplay constants
NUM_BOTS = 3
INITIAL_HEALTH = 5
SHIELD_HEALTH = 3

#Game status constants
TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN = 0, 1, 2, 3, 4

class Game:
    
    def __init__(self):
        self.p1_bots = [[INITIAL_HEALTH, 0] for _ in range(NUM_BOTS)]
        self.p2_bots = [[INITIAL_HEALTH, 0] for _ in range(NUM_BOTS)]
        self.status = TURN_OVER
        self.first_player_actions = None

    def process_turn(self, actions):
        if self.status == P1_PLAYED:
            p1_actions = self.first_player_actions
            p2_actions = actions
        else:
            p1_actions = actions
            p2_actions = self.first_player_actions

    def submit_turn(self, player_num, actions):
        assert len(actions) == NUM_BOTS
        if self.status == TURN_OVER: 
            self.first_player_actions = actions
            self.status = P1_PLAYED if player_num == 1 else P2_PLAYED
        elif (self.status == P2_PLAYED and player_num == 1) or (self.status == P1_PLAYED and player_num == 2):
            self.process_turn(actions)
            self.status = TURN_OVER