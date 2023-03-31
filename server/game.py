
#Gameplay constants
NUM_BOTS = 3
INITIAL_HEALTH = 5
SHIELD_HEALTH = 3

#Game status constants
TURN_OVER, P1_PLAYED, P2_PLAYED, P1_WIN, P2_WIN, TIE = 0, 1, 2, 3, 4, 5

#Illegal action constants
INVALID_TARGET, DEAD_TARGET, DEAD_BOT_ACTION, NOT_ENOUGH_AMMO = 0, 1, 2, 3

def process_actions(attacker_actions, attacker_bots, target_actions, target_bots):   
        new_target_healths = [bot[0] for bot in target_bots]

        #Tempoararily add shield health to all shielded bots
        for i, action in enumerate(target_actions): 
            if action["type"] == "shield": new_target_healths[i] += SHIELD_HEALTH

        errors = []
        for bot_id, action in enumerate(attacker_actions):
            bot = attacker_bots[bot_id]
            if action["type"] != "none" and bot[0] <= 0: errors.append((DEAD_BOT_ACTION, bot_id))
            elif action["type"] == "load": bot[1] += 1
            elif action["type"] == "launch":
                target, strength = action["target"], action["strength"]
                if strength > bot[1]: errors.append((NOT_ENOUGH_AMMO, bot_id))
                elif not 0 <= target < NUM_BOTS: errors.append((INVALID_TARGET, bot_id))
                elif target_bots[target][0] == 0: errors.append((DEAD_TARGET, bot_id))
                else:
                    new_target_healths[target] -= strength
                    if new_target_healths[target] < 0: new_target_healths[target] = 0
                    bot[1] -= strength
        
        #Reset bots to original health if they have shield health remaining
        for i, health in enumerate(new_target_healths):
            if health > target_bots[i][0]: new_target_healths[i] = target_bots[i][0]

        return new_target_healths, errors

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

        new_p2_healths, p1_errors = process_actions(p1_actions, self.p1_bots, p2_actions, self.p2_bots)
        new_p1_healths, p2_errors = process_actions(p2_actions, self.p2_bots, p1_actions, self.p1_bots)
        for bot_id, health in enumerate(new_p1_healths): self.p1_bots[bot_id][0] = health
        for bot_id, health in enumerate(new_p2_healths): self.p2_bots[bot_id][0] = health
        return p1_errors, p2_errors

    def check_victory(self):
        if not any(self.p1_bots) and not any(self.p2_bots):
            self.status = TIE
        elif not any(self.p1_bots):
            self.status = P2_WIN
        elif not any(self.p2_bots):
            self.status = P1_WIN
    
    def submit_turn(self, player_num, actions):
        assert len(actions) == NUM_BOTS

        if self.status == TURN_OVER: 
            #First player is submitting their actions, so do nothing besides record them for now
            self.first_player_actions = actions
            self.status = P1_PLAYED if player_num == 1 else P2_PLAYED
            return [], []
        elif (self.status == P2_PLAYED and player_num == 1) or (self.status == P1_PLAYED and player_num == 2):
            #Second player is submitting their actions, so process game round
            p1_errors, p2_errors = self.process_turn(actions)
            self.status = TURN_OVER
            self.check_victory()
            return p1_errors, p2_errors

    def __str__(self):
        return "P1: " + str(self.p1_bots) + ", P2: " + str(self.p2_bots)