import random


class Competitor:

    def __init__(self):
        self.username = "jimmy"
        self.round_number = 0

    def play_turn(self, controller):
        ammo = controller.get_my_bot_ammo(0)
        if ammo == 0: 
            controller.load(0)
            controller.load(1)
            controller.load(2)
        else: 
            controller.launch(0, 0, 1)
            controller.launch(1, 1, 1)
            controller.launch(2, 2, 1)
