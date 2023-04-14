import random


class Competitor:
    username = "user" # Change this!

    def __init__(self):
        # initialize a counter for the round number
        self.round_number = 0

    def play_turn(self, controller):
        self.round_number += 1

        # get the amount of ammo in our bot 0
        ammo = controller.get_my_bot_ammo(0)
        if ammo == 0: 
            # load ammo into bot 0
            controller.load(0)
            # load ammo into bot 1
            controller.load(1)
            # load ammo into bot 2
            controller.load(2)
        else: 
            # attack opponent bot 1 with your bot 0, using 1 ammo
            controller.attack(0, 1, 1)
            # attack opponent bot 2 with your bot 1, using 1 ammo
            controller.attack(1, 2, 1)
            # attack opponent bot 0 with your bot 2, using 1 ammo
            controller.attack(2, 0, 1)
