
class Controller:
    NUM_BOTS = 3

    def __init__(self):
        self.actions = [{"type": "none"} for _ in range(self.NUM_BOTS)]

    def reset(self):
        self.actions = [{"type": "none"} for _ in range(self.NUM_BOTS)]

    def load(self, bot):
        self.actions[bot] = {"type": "load"}

    def launch(self, bot, target_bot, attack_strength):
        self.actions[bot] = {"type": "launch", "target": target_bot, "strength": attack_strength}

    def shield(self, bot):
        self.actions[bot] = {"type": "shield"}

    def get_my_bot_health(self, bot):
        return self.player_state[bot][0]
    
    def get_my_bot_ammo(self, bot):
        return self.player_state[bot][1]

    def get_opponent_bot_health(self, bot):
        return self.opponent_state[bot][0]
    
    def get_opponent_bot_ammo(self, bot):
        return self.opponent_state[bot][1]
    
    