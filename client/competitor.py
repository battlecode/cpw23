import random

class Competitor:

    def __init__(self):
        self.username = "HONK HONK HONK"

    def play_turn(self, controller):
        count = 0
        while count:
            # murders the first bot
            if count == 0:
                controller.load(0)
                controller.load(1)
                controller.load(2)
            elif count == 6:
                controller.launch(0, 0, controller.get_my_bot_ammo(0))
                controller.launch(1, 0, controller.get_my_bot_ammo(1))
                controller.launch(2, 0, controller.get_my_bot_ammo(2))
            # murders the second bot
            elif count == 14:
                controller.launch(0, 1, controller.get_my_bot_ammo(0))
                controller.launch(1, 1, controller.get_my_bot_ammo(1))
                controller.launch(2, 1, controller.get_my_bot_ammo(2))
            # murders the third bot
            elif count == 22: 
                controller.launch(0, 2, controller.get_my_bot_ammo(0))
                controller.launch(1, 2, controller.get_my_bot_ammo(1))
                controller.launch(2, 2, controller.get_my_bot_ammo(2))
            # one bot loads up ammo and the other two bots shield themselves
            else:
                # determines all the bots that are alive
                otherBots = [bot for bot in [0, 1, 2] if controller.get_my_bot_health(bot) != 0]

                # picks a random bot to load         
                randomBot = otherBots[random.randint(0, len(otherBots))]
                otherBots.remove(randomBot)
                controller.load(randomBot)
                
                # all the other bots shield
                for bot in otherBots:
                    controller.shield(bot)
            

            count += 1
