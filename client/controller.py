
NUM_BOTS = 3

class Controller:

    def __init__(self, turn, my_bots, op_bots, op_actions):
        self.turn = turn
        self.actions = [{"type": "none"} for _ in range(NUM_BOTS)]
        self.player_state = my_bots
        self.opponent_healths = op_bots
        self.opponent_actions = op_actions

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
        return self.opponent_healths[bot]
    
    def get_opponent_previous_action(self, bot):
        """
        Returns the action the opponent bot at index bot took last round.
        Action is none for the first turn or if the specified bot is dead.
        Args:
            bot (int): index of bot
        Returns:
            dict of form {"type": "none/load/launch/shield", "target": number, "strength": number}
            For actions other than launch, there will be no target or strength key.
        """
        return self.opponent_actions[bot]