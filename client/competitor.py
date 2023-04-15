import random


class Competitor:
    username = "botbotbot" # Change this!
    random.seed(10234)

    def __init__(self):
        # initialize a counter for the round number
        self.round_number = 0
        self.f = open("output.txt", "a")

        self.prev_ally_health = [0] * 3
        self.prev_ammo = [0] * 3
        self.greedy = 0
        self.prev_attack = 0
        self.wait_attack = True
        self.general_wait_attack = True
        self.shield_prob = 1
        self.duel_standoff = False

    def attack(self, controller, ammo_counts, targets):
        if len(targets) == 2 and self.general_wait_attack:
            self.general_wait_attack = False
            return
        sorted_ammo = sorted(ammo_counts)
        total_used = 0
        curr_target = 0
        for i in range(3):
            tmp_target = curr_target % len(targets)
            if sorted_ammo[i][0] >= -targets[tmp_target][2] - total_used:
                controller.attack(-sorted_ammo[i][1], targets[tmp_target][3], -targets[tmp_target][2] - total_used)
            controller.attack(-sorted_ammo[i][1], targets[tmp_target][3], sorted_ammo[i][0])
            total_used += sorted_ammo[i][0]
            if total_used >= -targets[tmp_target][2]:
                curr_target += 1
                if curr_target >= len(targets):
                    total_used = -targets[curr_target % len(targets)][2] - 3
                else:
                    total_used = 0

    def duel_case(self, controller, ally, opponent):
        my_health = controller.get_my_bot_health(ally)
        my_ammo = controller.get_my_bot_ammo(ally)
        opponent_health = controller.get_opponent_bot_health(opponent)
        opponent_ammo = controller.get_opponent_bot_ammo(opponent)
        if my_ammo >= opponent_health + 3:
            if opponent_ammo >= my_health and self.wait_attack:
                controller.shield(ally)
                self.wait_attack = False
            controller.attack(ally, opponent, my_ammo)
            return
        if my_health - opponent_ammo > opponent_health + 3 - my_ammo:
            controller.load(ally)
            return
        if my_health - opponent_ammo + 3 < opponent_health - my_ammo:
            if my_health == opponent_ammo:
                controller.shield(ally)
                return
            if my_ammo >= opponent_health:
                if my_health >= opponent_ammo + 1:
                    controller.attack(ally, opponent, my_ammo)
                else:
                    controller.load(ally)
            return
        if opponent_ammo == my_health:
            if self.duel_standoff:
                prev_action = controller.get_opponent_previous_action(opponent)["type"] 
                if prev_action == "shield":
                    self.shield_prob -= 0.2
                elif prev_action == "load":
                    self.shield_prob -= 0.4
            if random.random() < self.shield_prob:
                controller.shield(ally)
            else:
                controller.attack(ally, opponent, my_ammo)
            self.duel_standoff = True
            return

            return
        if my_ammo >= opponent_health and my_health <= opponent_ammo - 1:
            if self.wait_attack:
                self.wait_attack = False
            else:
                controller.attack(ally, opponent, my_ammo)
                return
        controller.load(ally)

    def play_turn(self, controller):
        self.round_number += 1
        remaining_bots = 0

        for i in range(3):
            prev_act = controller.get_opponent_previous_action(i)
            tmp = sum(self.prev_ammo)
            if prev_act["type"] == "launch":
                self.prev_attack = min(prev_act["target"], 1)
                if tmp >= min(self.prev_ally_health):
                    self.greedy = 0.6 if self.greedy < 0.6 else self.greedy + 0.2
            elif prev_act["type"] != "launch" and tmp >= min(self.prev_ally_health):
                self.greedy = 0.6 if self.greedy < 0.6 else self.greedy + 0.2
            if controller.get_my_bot_health(i) > 0:
                remaining_bots += 1

        total_ammo = 0
        ammo_counts = [0] * 3
        enemy_ammo = [0] * 3
        total_enemy_ammo = 0
        for i in range(3):
            ammo_counts[i] = (controller.get_my_bot_ammo(i), -i)
            total_ammo += ammo_counts[i][0]
            enemy_ammo[i] = controller.get_opponent_bot_ammo(i)
            total_enemy_ammo += enemy_ammo[i]

        for i in range(3):
            controller.load(i)

        rand = random.random()
        if self.greedy == 0:
            self.greedy = 0.8 * (3 - remaining_bots) / 3

        if rand > self.greedy:
            # shield_prio = [0] * 3
            # for i in range(3):
            #     curr_health = controller.get_my_bot_health(i)
            #     if total_enemy_ammo >= curr_health and total_enemy_ammo < curr_health + 3:
            #         shield_prio[i] = (5 - (self.prev_attack - i) ** 2) + controller.get_my_bot_ammo(i)

            # shield_bot = (0, -1)
            # for i in range(3):
            #     if shield_prio[i] > 0 and shield_prio[i] > shield_bot[0]:
            #         shield_bot = (shield_prio[i], i)
            # if shield_bot[1] >= 0:
            #     controller.shield(shield_bot[1])
            for i in range(3):
                controller.shield(i)

        weakest_target = (1000, -1)
        targets = []
        for i in range(3):
            enemy_health = controller.get_opponent_bot_health(i)
            if enemy_health == 0:
                continue
            targets.append((not enemy_health <= controller.get_opponent_bot_ammo(i), -controller.get_opponent_bot_ammo(i), -enemy_health, i))
        targets = sorted(targets)
        weakest_target = (-targets[0][2], targets[0][3]) if len(targets) > 0 else False

        if total_ammo >= weakest_target[0]:
            rand = random.random()
            if weakest_target and rand < controller.get_opponent_bot_ammo(weakest_target[1]) / 6:
                self.attack(controller, ammo_counts, targets)

        if total_ammo >= weakest_target[0] + 3:
            self.attack(controller, ammo_counts, targets)

        for i in range(3):
            if total_enemy_ammo >= controller.get_my_bot_health(i):
                attack_prob = controller.get_my_bot_ammo(i) / 5
                if random.random() < attack_prob and weakest_target:
                    controller.attack(i, weakest_target[1], controller.get_my_bot_ammo(i))

        if remaining_bots == 1 and len(targets) == 1:
            for i in range(3):
                if controller.get_my_bot_health(i) > 0:
                    self.duel_case(controller, i, targets[0][3])
                    break

        for i in range(3):
            self.prev_ammo[i] = controller.get_opponent_bot_ammo(i)
            self.prev_ally_health[i] = controller.get_my_bot_health(i)

