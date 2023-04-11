import random

class Competitor:

    def __init__(self):
        self.username = "HONK HONK HONK"
        self.count = 0

    # def play_turn(self, controller):
    #     kill = 0
    #     if self.count == 0:
    #         controller.load(0)
    #         controller.load(1)
    #         controller.load(2)
    #     else:
    #         totalAmmo = 0
    #         for bot in [0, 1, 2]:
    #             totalAmmo += controller.get_my_bot_ammo(bot)
    #         if totalAmmo == 8:
    #             controller.launch(0, kill, controller.get_my_bot_ammo(0))
    #             controller.launch(1, kill, controller.get_my_bot_ammo(1))
    #             controller.launch(2, kill, controller.get_my_bot_ammo(2))
    #             kill += 1
    #         else:
    #             otherBots = [bot for bot in [0, 1, 2] if controller.get_my_bot_health(bot) != 0]
                # randomBot = otherBots[random.randint(0, len(otherBots))]
                # otherBots.remove(randomBot)
                # controller.load(randomBot)
                # for bot in otherBots:
                #     controller.shield(bot)

    #     self.count += 1

    def play_turn(self, controller):
        kill = 0

        oneAction = []
        twoAction = []

        oneAmmo = []
        twoAmmo = []

        if self.count == 0 or self.count == 1:
            controller.load(0)
            controller.load(1)
            controller.load(2)
        elif self.count == 2:
            controller.load(0)
            controller.load(1)
            controller.shield(2)
        elif self.count == 3:
            controller.launch(0, kill, controller.get_my_bot_ammo(0))
            controller.launch(0, kill, controller.get_my_bot_ammo(1))
            controller.launch(0, kill, controller.get_my_bot_ammo(2))
        else:
            aliveBots = [bot for bot in [0, 1, 2] if controller.get_my_bot_health(bot) != 0]
            totalAmmo = 0
            shield = False

            # if the first enemy bot's health is 0, we move to kill the very last bot
            if controller.get_opponent_bot_health(1) == 0:
                kill += 1

            # one-shots the next bot
            if totalAmmo == 8:
                controller.launch(0, kill, controller.get_my_bot_ammo(0))
                controller.launch(1, kill, controller.get_my_bot_ammo(1))
                controller.launch(2, kill, controller.get_my_bot_ammo(2))
                kill += 1
                shield = True
            # protects all the bots immediately after one-shotting
            elif shield:
                for bot in aliveBots:
                    controller.shield(bot)
                shield = False
            # all the alive bots will load once either of the bots has fired
            elif oneAction[-1] == "fire" or twoAction[-1] == "fire":
                for bot in aliveBots: controller.load(bot)
            # if the ammo of the two bots is greater than or equal to 6, we try to attack them
            elif oneAmmo[-1] + twoAmmo[-1] >= 5:
                health = controller.get_opponent_bot_health(kill)
                for bot in aliveBots:
                    controller.launch(bot, kill, min(controller.get_my_bot_ammo(bot), health))
                    health -= controller.get_my_bot_ammo(0)
            #  if none of the above statements are true, picks one random bot to load and all the other bots shield
            else:
                randomBot = aliveBots[random.randint(0, len(aliveBots))]
                aliveBots.remove(randomBot)
                controller.load(randomBot)
                for bot in aliveBots:
                    controller.shield(bot)


        oneAction.append(controller.get_previous_opponent_action(1)["type"])
        twoAction.append(controller.get_previous_opponent_action(2)["type"])
        oneAmmo.append(controller.get_opponent_bot_ammo(1))
        twoAmmo.append(controller.get_opponent_bot_ammo(2))
            
        self.count += 1

    