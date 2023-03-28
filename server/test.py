from game import Game

game = Game()

for i in range(10):
    game.submit_turn(1, [{"type": "load"}, {"type": "load"}, {"type": "load"}])
    game.submit_turn(2, [{"type": "load"}, {"type": "load"}, {"type": "load"}])

print(game)

game.submit_turn(1, [{"type": "launch", "target": 1, "strength": 2}, {"type": "launch", "target": 1, "strength": 12}, {"type": "load"}])
game.submit_turn(2, [{"type": "load"}, {"type": "launch", "target": 0, "strength": 1}, {"type": "load"}])

print(game)