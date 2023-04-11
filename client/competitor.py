import random

SHIELD_AMOUNT = 3
ID = 0
HEALTH = 1
AMMO = 2


class Competitor:

    prev_opp_sorted = None
    prev_my_sorted = None
    protect_idx = [0 for _ in range(3)]
    hurt_idx = [0 for _ in range(3)]
    dead = set()
    opp_dead = set()

    def __init__(self):
        self.username = "jimmy"
        self.turn = 0

    def one_shot_bot(self, controller, opp_bot, my_bots_sorted, bot_actions, shielded=True):
        tot = controller.get_opponent_bot_health(opp_bot)
        if shielded:
            tot += 3
        new_sort = sorted(my_bots_sorted, key=lambda x:(x[HEALTH], x[AMMO]))
        for (id, health, ammo) in new_sort:
            if tot == 0:
                break
            shoot_amount = min(tot, ammo)
            controller.launch(id, opp_bot, shoot_amount)
            bot_actions[id] = "LAUNCH"
            tot -= shoot_amount
        return

    def play_turn(self, controller):
        bot_actions = dict()
        self.turn += 1

        if prev_opp_sorted is not None and prev_my_sorted is not None:
            attacked = dict()
            # Which index do they protect the most?
            for i, (id, health, ammo) in enumerate(prev_opp_sorted):
                prev_action = controller.get_previous_opponent_action(id)
                if prev_action["type"] == "shield":
                    self.protect_idx[i] += 1
                if prev_action["type"] == "attack":
                    attacked[prev_action["target"]] = attacked.get(prev_action["target"], 0) + 1


            # Which index do they attack the most?
            for i, (id, health, ammo) in enumerate(prev_my_sorted):
                self.protect_idx[i] + attacked.get(id, 0)


        for i in range(controller.NUM_BOTS):
            controller.load(i)
            bot_actions[i] = "LOAD"
        if self.turn == 1:
            return
        
        for i in range(controller.NUM_BOTS):
            if self.get_my_bot_health(i) == 0:
                self.dead.add(i)
            if self.get_opponent_bot_health(i) == 0:
                self.opp_dead.add(i)
        
        opp = [(i, controller.get_opponent_bot_health(i), controller.get_opponent_bot_ammo(i)) for i in range(controller.NUM_BOTS) if i not in opp.dead]
        opp_tot_ammo = sum([i[AMMO] for i in opp])
        my_bots = [(i, controller.get_my_bot_health(i), controller.get_my_bot_ammo(i)) for i in range(controller.NUM_BOTS) if i not in self.dead]
        my_tot_ammo = sum([i[AMMO] for i in my_bots])
        opp_sorted = sorted(opp, key=lambda x: (x[HEALTH], -x[AMMO]))
        my_sorted = sorted(my_bots, key=lambda x: (x[HEALTH], -x[AMMO]))


        def attack():
            # Find which bots I can oneshot
            opp_one_shot_shielded = set()
            opp_one_shot = set()
            for i, (id, health, _) in enumerate(opp_sorted):
                assert(health != 0)
                if health <= my_tot_ammo:
                    opp_one_shot.add(id)
                if health + 3 <= my_tot_ammo:
                    opp_one_shot_shielded.add(id)

            max_protect = max(self.protect_idx)
            # If they are unlikely to protect a bot that I can oneshot when it's not shielded attack that, otherwise attack the other
            for i, opp in enumerate(opp_sorted[::-1]):
                if opp[ID] in opp_one_shot:
                    if self.protect_idx[i] < max_protect / 3:
                        print("Attacking bot at index {i} with id {opp[ID]} and health {opp[HEALTH]}")
                        self.one_shot_bot(self, controller, opp[ID], my_sorted, bot_actions, shielded=False)
                        return
                if opp[ID] in opp_one_shot_shielded:
                    print("Attacking bot at index {i} with id {opp[ID]} and health {opp[HEALTH]}")
                    self.one_shot_bot(self, controller, opp[ID], my_sorted, bot_actions)
                    return

        attack()
        
        my_tot_health = sum([i[HEALTH] for i in my_bots])
        opp_tot_health = sum([i[HEALTH] for i in opp])

        # If I have more total health, trade, otherwise don't
        ATTACK_MODE = my_tot_health >= opp_tot_health

        # Block their attack on the bot they seem most likely to attack
        max_hurt = max(self.hurt_idx)
        max_index = self.hurt_idx.index(max_hurt)

        if opp_tot_ammo > my_sorted[max_index][HEALTH]:
            id = my_sorted[max_index][ID]
            if opp_tot_ammo < my_sorted[max_index][HEALTH] + SHIELD_AMOUNT:
                if not ATTACK_MODE or bot_actions[id] != "LAUNCH":
                    bot_actions[id] = "SHIELD"
                    controller.shield(id)


        print(bot_actions)
        prev_opp_sorted = opp_sorted
        prev_my_sorted = my_sorted

        prev_opp_sorted = [i/self.turn for i in prev_opp_sorted]
        prev_my_sorted = [i/self.turn for i in prev_my_sorted]

