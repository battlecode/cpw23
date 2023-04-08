
class Controller:
    NUM_BOTS = 3
    NO_ERROR, INVALID_TARGET, DEAD_TARGET, DEAD_BOT_ACTION, NOT_ENOUGH_AMMO = -1, 0, 1, 2, 3

    def __init__(self):
        self.prev_round_errors = [-1 for _ in range(self.NUM_BOTS)]
        self.actions = [{"type": "none"} for _ in range(self.NUM_BOTS)]

    def reset(self):
        self.actions = [{"type": "none"} for _ in range(self.NUM_BOTS)]

    def load(self, bot):
        """
        Takes load action, adds one to ammo of bot
        Args:
            bot (int): index of bot
        """
        self.actions[bot] = {"type": "load"}

    def launch(self, bot, target_bot, attack_strength):
        """
        Takes launch action
        Args:
            bot (int): index of bot
            target_bot (int): index of opponents target bot
            attack_strenght (int): amount of ammo to attack with
        """
        self.actions[bot] = {"type": "launch", "target": target_bot, "strength": attack_strength}

    def shield(self, bot):
        """
        Takes shield action
        Args:
            bot (int): index of bot
        """
        self.actions[bot] = {"type": "shield"}

    def get_my_bot_health(self, bot):
        """
        Returns health for teams bot with index bot
        Args:
            bot (int): index of bot
        Returns:
            (int): health for teams bot
        """
        return self.player_state[bot][0]
    
    def get_my_bot_ammo(self, bot):
        """
        Returns ammo for teams bot with index bot
        Args:
            bot (int): index of bot
        Returns:
            (int): ammo for teams bot
        """
        return self.player_state[bot][1]

    def get_opponent_bot_health(self, bot):
        """
        Returns health for opponents bot with index bot
        Args:
            bot (int): index of bot
        Returns:
            (int): health for opponent bot
        """
        return self.opponent_state[bot][0]
    
    def get_opponent_bot_ammo(self, bot):
        """
        Returns ammo for opponents bot with index bot
        Args:
            bot (int): index of bot
        Returns:
            (int): ammo for opponent bot
        """
        return self.opponent_state[bot][1]
    
    def get_prev_round_errors(self):
        """
        Returns error codes from previous round
        Returns:
            (list[int]): element at i corresponds to error code for bot i in previous round
        """
        return self.prev_round_errors
    
    