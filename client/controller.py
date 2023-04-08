
NUM_BOTS = 3

class Controller:

    def __init__(self, initial_state):
        self.actions = [{"type": "none"} for _ in range(NUM_BOTS)]
        self.player_state = initial_state
        self.opponent_healths = [bot[0] for bot in initial_state]

    def reset(self):
        '''
        Sets all robot actions to none
        '''
        self.actions = [{"type": "none"} for _ in range(NUM_BOTS)]

    def load(self, bot):
        '''
        Instructs the bot to load on this turn.
        '''
        self.actions[bot] = {"type": "load"}

    def launch(self, bot, target_bot, attack_strength):
        '''
        Instructs the bot to attack target_bot using attack_strength ammo

        if attack strength greater than ammo, use all ammo
        '''
        self.actions[bot] = {"type": "launch", "target": target_bot, "strength": attack_strength}

    def shield(self, bot):
        '''
        Instructs the bot to shield on this turn.
        '''
        self.actions[bot] = {"type": "shield"}

    def get_my_bot_health(self, bot):
        '''
        Returns the health of the given bot
        '''
        return self.player_state[bot][0]
    
    def get_my_bot_ammo(self, bot):
        '''
        Returns the available ammo of the given bot.
        '''
        return self.player_state[bot][1]

    def get_opponent_bot_health(self, bot):
        '''
        Returns the health of the given opponent bot.
        '''
        return self.opponent_healths(bot)