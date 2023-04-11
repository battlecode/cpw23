import random

ID = 0
HEALTH = 1
AMMO = 2


class Competitor:

    dead = set()
    opp_dead = set()

    def __init__(self):
        self.username = "jimmy"
        self.turn = 0

    def play_turn(self, controller):
        self.turn += 1

        for i in range(controller.NUM_BOTS):
            controller.load(i)
        if self.turn == 1:
            return
        
        for i in range(controller.NUM_BOTS):
            if controller.get_my_bot_health(i) == 0:
                self.dead.add(i)
            if controller.get_opponent_bot_health(i) == 0:
                self.opp_dead.add(i)
        
        my_bots = [(i, controller.get_my_bot_health(i), controller.get_my_bot_ammo(i)) for i in range(controller.NUM_BOTS) if i not in self.dead]
        possible_opps = [i for i in range(controller.NUM_BOTS) if i not in self.opp_dead]

        for bot in my_bots:
            possible_actions = ["SHIELD", "LOAD"]
            if bot[AMMO] > 0:
                possible_actions.append("LAUNCH")
            action = random.choice(possible_actions)
            if action == "LOAD":
                continue
            elif action == "SHIELD":
                controller.shield(bot[ID])
            elif action == "LAUNCH":
                assert bot[AMMO] > 0
                opp_to_attack = random.choice(possible_opps)
                attack_amount = min(controller.get_my_bot_ammo(bot[ID]), controller.get_opponent_bot_health(opp_to_attack))
                controller.launch(bot[ID], opp_to_attack, attack_amount)
            

            

