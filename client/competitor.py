import random

class Competitor:

    def __init__(self):
        self.username = "jimmy"

    def play_turn(self, controller):
        ammo = controller.get_my_bot_ammo(0)
        if ammo == 0: controller.load(0)
        else: controller.launch(0, random.randrange(3), 1)
