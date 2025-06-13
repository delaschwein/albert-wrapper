from albert_utils import (
    convert,
    convert_to_hex,
    POWER_NAMES,
    decimal_to_hex,
    daidefy_order,
    cal_remaining_len,
    daidefy_unit,
    dipnet_order,
    daidefy_location,
    sanitize_daide,
    DAIDE2HEX,
)
import socket
import json
from diplomacy.utils.game_phase_data import GamePhaseData
from diplomacy.client.network_game import NetworkGame
from diplomacy.client.connection import connect
import asyncio
from chiron_utils.bots.baseline_bot import BaselineBot, BotType
from abc import ABC
from typing import Sequence, List
import os
from diplomacy.utils.constants import SuggestionType
from diplomacy import Message
import traceback
import tomllib
from chiron_utils.daide2eng import gen_english
from chiron_utils.utils import is_valid_daide_message
import logging
import diplomacy
import sys
from queue import Queue




async def run():
    connection = await connect("173.79.1.178", 8433, False)
    channel = await connection.authenticate("admin", "password")
    POWERS = ["AUSTRIA", "ENGLAND", "FRANCE", "GERMANY", "ITALY", "RUSSIA", "TURKEY"]

    names = [f"ADMIN_{i}" for i in POWERS]

    for nn in names:
        await channel.promote_administrator(username=nn)
    print("Promoted all powers to admin")


if __name__ == "__main__":
    asyncio.run(run())
