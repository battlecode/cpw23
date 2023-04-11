import random


class Competitor:

    def __init__(self):
        self.username = "jimmy"
        self.round_number = 0

    def play_turn(self, controller):
        self.round_number += 1
        for i in range(controller.NUM_BOTS):
            ammo = controller.get_my_bot_ammo(i)
            if ammo == 0: controller.load(i)
            else: controller.launch(i, random.randrange(3), 1)
