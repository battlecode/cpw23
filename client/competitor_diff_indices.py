import random

ID = 0
HEALTH = 1
AMMO = 2


class Competitor:

    prev_opp = None
    prev_my = None
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

        if self.prev_opp_sorted is not None and self.prev_my_sorted is not None:
            attacked = dict()
            # Which index do they protect the most?
            for id, health, ammo in self.prev_opp_sorted:
                prev_action = controller.get_previous_opponent_action(id)
                if prev_action["type"] == "shield":
                    self.protect_idx[id] += 1
                if prev_action["type"] == "attack":
                    attacked[prev_action["target"]] = attacked.get(prev_action["target"], 0) + 1


            # Which index do they attack the most?
            for id, health, ammo in self.prev_my_sorted:
                self.protect_idx[id] + attacked.get(id, 0)


        for i in range(controller.NUM_BOTS):
            controller.load(i)
            bot_actions[i] = "LOAD"
        if self.turn == 1:
            return
        
        for i in range(controller.NUM_BOTS):
            if controller.get_my_bot_health(i) == 0:
                self.dead.add(i)
            if controller.get_opponent_bot_health(i) == 0:
                self.opp_dead.add(i)
        
        opps = [(i, controller.get_opponent_bot_health(i), controller.get_opponent_bot_ammo(i)) for i in range(controller.NUM_BOTS) if i not in self.opp_dead]
        opp_tot_ammo = sum([i[AMMO] for i in opps])
        my_bots = [(i, controller.get_my_bot_health(i), controller.get_my_bot_ammo(i)) for i in range(controller.NUM_BOTS) if i not in self.dead]
        my_tot_ammo = sum([i[AMMO] for i in my_bots])


        def attack():
            # Find which bots I can oneshot
            opp_one_shot_shielded = set()
            opp_one_shot = set()
            for id, health, _ in opps:
                assert(health != 0)
                if health <= my_tot_ammo:
                    opp_one_shot.add(id)
                if health + 3 <= my_tot_ammo:
                    opp_one_shot_shielded.add(id)

            max_protect = max(self.protect_idx)
            # If they are unlikely to protect a bot that I can oneshot when it's not shielded attack that, otherwise attack the other
            for o in opps[::-1]:
                if opps[ID] in opp_one_shot:
                    if self.protect_idx[i] < max_protect / 3:
                        print("Attacking bot at index {i} with id {o[ID]} and health {o[HEALTH]}")
                        self.one_shot_bot(self, controller, o[ID], my_bots, bot_actions, shielded=False)
                        return
                if o[ID] in opp_one_shot_shielded:
                    print("Attacking bot at index {i} with id {opp[ID]} and health {opp[HEALTH]}")
                    self.one_shot_bot(self, controller, o[ID], my_bots, bot_actions)
                    return

        attack()
        
        my_tot_health = sum([i[HEALTH] for i in my_bots])
        opp_tot_health = sum([i[HEALTH] for i in opps])

        # If I have more total health, trade, otherwise don't
        ATTACK_MODE = my_tot_health >= opp_tot_health

        # Block their attack on the bot they seem most likely to attack
        max_hurt = max(self.hurt_idx)
        max_index = self.hurt_idx.index(max_hurt)

        if opp_tot_ammo > my_bots[max_index][HEALTH]:
            id = my_bots[max_index][ID]
            if opp_tot_ammo < my_bots[max_index][HEALTH] + controller.SHIELD_AMOUNT:
                if not ATTACK_MODE or bot_actions[id] != "LAUNCH":
                    bot_actions[id] = "SHIELD"
                    controller.shield(id)


        print(bot_actions)
        self.prev_opp = opps
        self.prev_my = my_bots

        self.prev_opp = [i/self.turn for i in self.prev_opp]
        self.prev_my = [i/self.turn for i in self.prev_my]

