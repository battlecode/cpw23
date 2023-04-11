import random


class Competitor:

    def __init__(self):
       self.username = "rghc"
       self.round_num = 0
       self.shield_times = 0 #counts # of times opponent shields for probabilistic shooting
       self.was_attacked = []
    
    def play_turn(self, controller):
       self.round_num += 1
      
   #    ammo = controller.get_my_bot_ammo(0)
    #   if ammo == 0: controller.load(0)
     #  else: controller.launch(0, random.randrange(3), 1)
       opponent_actions = [controller.get_previous_opponent_action(i) for i in [0, 1, 2]]
       op_shielded = False
       for d in opponent_actions:
               if d["type"] == "shield":
                   op_shielded = True
       if op_shielded:
           self.shield_times += 1
       if self.round_num == 1:
           for i in range(3):
               controller.load(i)
       elif self.round_num == 2:
           
           controller.shield(0)
           controller.load(1)
           controller.load(2)
       else:
          
           target = max((i for i in range(3)), key = controller.get_opponent_bot_ammo)
           tot_ammo = sum(controller.get_my_bot_ammo(i) for i in range(3))
          
           #default load
           controller.load(0)
           controller.load(1)
           controller.load(2)
          
           #shield if attacked 2 rounds ago
           for bot, round in self.was_attacked:
               if round == self.round_num -2:
                   controller.shield(bot)


           #shoot if kill!
           if tot_ammo >= controller.get_opponent_bot_health(target) + self.shield_times/self.round_num*3:
               tot_attack = int(controller.get_opponent_bot_health(target) - .0001 + self.shield_times/self.round_num*3)+1
               cur_attack = 0
               for i in range(3):
                   if cur_attack < tot_attack:
                       amt = min(tot_attack-cur_attack, controller.get_my_bot_ammo(i))
                       cur_attack += amt
                       controller.launch(i, target, amt)
          
           self.was_attacked = [(bot, round) for (bot, round) in self.was_attacked if round != self.round_num -2]
          
           #update self.was_attacked w/ previous enemy actions
           for d in opponent_actions:
               if d["type"] == "launch":
                   self.was_attacked.append((d["target"], self.round_num))

