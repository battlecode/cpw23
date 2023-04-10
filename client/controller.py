
NUM_BOTS = 3

class Controller:

    def __init__(self, turn, my_bots, op_bots):
        self.turn = turn
        self.actions = [{"type": "none"} for _ in range(NUM_BOTS)]
        self.player_state = my_bots
        self.opponent_healths = op_bots

    def reset(self):
        self.actions = [{"type": "none"} for _ in range(NUM_BOTS)]

    def load(self, bot):
        self.actions[bot] = {"type": "load"}

    def launch(self, bot, target_bot, attack_strength):
        self.actions[bot] = {"type": "launch", "target": target_bot, "strength": attack_strength}

    def shield(self, bot):
        self.actions[bot] = {"type": "shield"}
    
    def get_turn_num(self):
        return self.turn

    def get_my_bot_health(self, bot):
        return self.player_state[bot][0]
    
    def get_my_bot_ammo(self, bot):
        return self.player_state[bot][1]

    def get_opponent_bot_health(self, bot):
        return self.opponent_healths(bot)