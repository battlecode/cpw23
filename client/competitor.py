import random


class Competitor:
    username = "botbotbot" # Change this!
    random.seed(10234)

    def __init__(self):
        # initialize a counter for the round number
        self.round_number = 0

        self.attack_likelihood = [0] * 3
        self.block_likelihood = [0] * 3
        self.load_likelihood = [0] * 3

    def play_turn(self, controller):
        self.round_number += 1

        total_ammo = 0
        ammo_counts = [0] * 3
        enemy_ammo = [0] * 3
        total_enemy_ammo = 0
        for i in range(3):
            ammo_counts[i] = (controller.get_my_bot_ammo(i), -i)
            total_ammo += ammo_counts[i][0]
            enemy_ammo[i] = controller.get_opponent_bot_ammo(i)
            total_enemy_ammo += enemy_ammo[i]

        summed_likelihood = [0] * 3
        for i in range(3):
            summed_likelihood[i] = attack_likelihood[i] + block_likelihood[i] + load_likelihood[i]

        weakest_target = ((1 << 30), -1)
        for i in range(3):
            enemy_health = controller.get_opponent_bot_health(i)
            if enemy_health < weakest_target[0]:
                weakest_target = (enemy_health, i)
        if total_ammo >= weakest_target[0] + 3:
            sorted_ammo = sorted(ammo)
            total_used = 0
            for i in range(3):
                if sorted_ammo[i] >= weakest_target[0] + 3 - total_used:
                    controller.attack(-sorted_ammo[i][1], weakest_target[0] + 3 - total_used)
                    break
                controller.attack(-sorted_ammo[i][1], sorted_ammo[i][0])
                total_used += sorted_ammo[i][0]

        for i in range(3):
            curr_health = controller.get_my_bot_health(i)
            if total_enemy_ammo >= curr_health and total_enemy_ammo < curr_health + 3:
                controller.block(i)

        for i in range(3):
            controller.load(i)
