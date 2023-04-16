import random

def f(x):
    return (x + 8) % 9 + 1

class Competitor:
    username = "skynet"

    def play_turn(self, controller):
        # Get state information
        my_health = list(map(controller.get_my_bot_health, range(3)))
        my_ammo = list(map(controller.get_my_bot_ammo, range(3)))
        opp_health = list(map(controller.get_opponent_bot_health, range(3)))
        opp_ammo = list(map(controller.get_opponent_bot_ammo, range(3)))

        # Calculate actions
        actions = ["vibe", "vibe", "vibe"]
        for i in range(3):
            if my_health[i] <= sum(opp_ammo):
                actions[i] = "shield"
        if (
            min(f(x) for x in my_health) <= sum(opp_ammo) - 3 or
            min(f(x) for x in opp_health) <= sum(my_ammo) - 3
        ):
            for i in range(3):
                if my_ammo[i]:
                    actions[i] = "attack"
        for i in range(3):
            if actions[i] == "vibe":
                actions[i] = "load"

        # Add some randomness
        for i in range(3):
            if actions[i] == "load" and sum(opp_ammo) > 0 and random.random() < 0.2:
                actions[i] = "shield"
            if actions[i] == "shield" and random.random() < 0.2:
                actions[i] = "load"
        if sum(my_ammo) >= max(4, min(f(x) for x in opp_health)) and random.random() < 0.2:
            for i in range(3):
                if my_ammo[i]:
                    actions[i] = "attack"

        # Pick a target for attack
        target, *_ = sorted(range(3), key=lambda i: f(opp_health[i])+random.random())

        # Distribute attack ammo
        attack_ammo = [0, 0, 0]
        remain = opp_health[target] + 3
        attackers = sorted((i for i in range(3) if actions[i] == "attack"), key=lambda i: my_health[i]+random.random())
        for i in attackers:
            use = min(remain, my_ammo[i])
            if use:
                attack_ammo[i] = use
                remain -= use
            else:
                actions[i] = "load"

        # Go
        for i in range(3):
            match actions[i]:
                case "vibe":
                    pass
                case "shield":
                    controller.shield(i)
                case "load":
                    controller.load(i)
                case "attack":
                    controller.attack(i, target, attack_ammo[i])
