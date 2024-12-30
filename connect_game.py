from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils import strings as diplomacy_strings
from diplomacy.utils.constants import SuggestionType
import json
from typing import Any, List, Mapping, Optional, Set
from diplomacy.client.connection import connect
from diplomacy.client.network_game import NetworkGame
import asyncio
from chiron_utils.bots.baseline_bot import BaselineBot, BotType
from abc import ABC
from typing import List, Optional, Sequence


def serialize_message_dict(message_dict: Mapping[str, Any]) -> str:
    json.dumps(message_dict, ensure_ascii=False, separators=(",", ":"))


async def suggest_message(self, recipient: str, message: str) -> None:

    """
    suggestion type
    /*
         0: NONE
         1: MESSAGE
         2: MOVE
         4: COMMENTARY
        */
    """
    

class CiceroBot(BaselineBot, ABC):
    async def gen_orders(self) -> List[str]:
        return []

    async def do_messaging_round(self, orders: Sequence[str]) -> List[str]:
        return []


class CiceroAdvisor(CiceroBot):
    """Advisor form of `CiceroBot`."""

    bot_type = BotType.ADVISOR
    suggestion_type = SuggestionType.MOVE



async def run():
    credentials = ("admin", "password")
    connection = await connect("localhost", 8433, False)
    channel = await connection.authenticate(*credentials)


    game: NetworkGame = await channel.join_game(game_id="test1")

    #await game.set_orders(orders=["F TRI - ADR"])
    
    cicero = CiceroAdvisor("AUSTRIA", game)
    await cicero.declare_suggestion_type()
    await cicero.suggest_orders(orders=["F TRI - ADR"])
    #await cicero.suggest_commentary("AUSTRIA", "I am a bot44")
    print("done")
    exit(0)

    

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()