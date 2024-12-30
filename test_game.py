from diplomacy import Game
from diplomacy.utils.game_phase_data import GamePhaseData
import pprint
from server_imitator import build_SCO, build_NOW, build_ORD, build_MRT

game = Game()

#current_phase = game.get_phase_data()
#build_NOW(GamePhaseData.to_dict(current_phase))
# S1901M

game.set_orders("RUSSIA", ["F SEV - BLA"])
game.set_orders("AUSTRIA", ["F TRI - ADR"])
game.set_orders("TURKEY", ["F ANK - CON", "A CON - SMY", "A SMY - ARM"])
assert "F SEV - BLA" in game.get_all_possible_orders()["SEV"]
assert "F TRI - ADR" in game.get_all_possible_orders()["TRI"]
assert "F ANK - CON" in game.get_all_possible_orders()["ANK"]
assert "A CON - ANK" in game.get_all_possible_orders()["CON"]
game.process()
# F1901M
game.set_orders("AUSTRIA", ["F ADR - ION"])
assert "F ADR - ION" in game.get_all_possible_orders()["ADR"]

game.process()
game.process()
# S1902M

game.set_orders("AUSTRIA", ["F ION - AEG"])
assert "F ION - AEG" in game.get_all_possible_orders()["ION"]
game.process()
game.process()
game.set_orders("AUSTRIA", ["F AEG - CON"])
game.set_orders("RUSSIA", ["F BLA S F AEG - CON"])
assert "F AEG - CON" in game.get_all_possible_orders()["AEG"]
assert "F BLA S F AEG - CON" in game.get_all_possible_orders()["BLA"]
#pprint.pprint(game.get_all_possible_orders()["CON"])
#game.process()

#build_NOW(game)
#pprint.pprint(GamePhaseData.to_dict(current_phase))
#pprint.pprint(game.get_all_possible_orders()["CON"])

#print(game.get_current_phase())

#phase_history = game.get_phase_history()
#phase_list = [GamePhaseData.to_dict(x) for x in phase_history]

#pprint.pprint(phase_list[0])
current_phase = game.get_phase_data()
pprint.pprint(GamePhaseData.to_dict(current_phase))
print(game._find_next_phase())
print(check(game))
#build_SCO(GamePhaseData.to_dict(current_phase))