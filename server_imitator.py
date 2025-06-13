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


async def send_response_with_retry(client_socket, loop, response):
    if LOG:
        with open("log.txt", "a") as f:
            if isinstance(response, bytes):
                f.write(f"s -> c: {" ".join(convert(response.hex()))}\n")
            else:
                f.write(f"s -> c: {" ".join(convert(response))}\n")
            f.write(f"s -> c: {response}\n")

    return await loop.sock_sendall(
        client_socket,
        response if isinstance(response, bytes) else bytes.fromhex(response),
    )

async def set_game_orders(game, orders):
    return game.set_orders(orders=orders)
    

async def send_game_message(game, message):
    return game.send_game_message(message=message)
    

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

PRESS = config["albert"]["press"]
LOG = config["logging"]["log"]
HOSTNAME = config["paquette"]["hostname"]
PORT = config["paquette"]["port"]
GAME_ID = config["paquette"]["game_id"]
USE_SSL = config["paquette"]["use_ssl"]
USE_NL = config["albert"]["use_nl"]
TO_ADVISE = config["albert"]["to_advise"]
TO_PLAY = config["albert"]["to_play"]
TO_ENGINE = config["albert"]["to_engine"]
TO_COMMENT = config["albert"]["to_comment"]
PREDICT_OPPONENT_MOVE = len(TO_COMMENT)

predict_orders = {}



not_assigned_powers = [
    x for x in ["AUSTRIA", "ENGLAND", "FRANCE", "GERMANY", "ITALY", "RUSSIA", "TURKEY"] if x not in TO_ENGINE
]

power_queues = {
    "TO_ENGINE": Queue(),
    "NOT_ASSIGNED": Queue(),
}

for power in TO_ENGINE:
    power_queues["TO_ENGINE"].put(power)
for power in not_assigned_powers:
    power_queues["NOT_ASSIGNED"].put(power)

POWERS_ABBRS = {v: k for k, v in POWER_NAMES.items()}
DESIGNATED_ALBERT_POWER_ABBRS = list(POWER_NAMES.values())

with open("mapdef.json", "r") as f:
    MAPDEF = json.load(f)

with open("scs.json", "r") as f:
    SUPPLY_CENTERS = json.load(f)

"""
    NOTE: as long as DM prefix is >= 512 && < 768 it is valid
"""

def tokenize(orders):
    """
    convert a list of orders e.g.,["(", "(", "AUS", "AMY", "BUD", ")", "MTO", "VIE", ")"] to a list of lists e.g., [["(", "(", "AUS", "AMY", "BUD", ")", "MTO", "VIE", ")"]]
        or split powers from press
    """

    results = []
    q = []
    num_unclosed_parens = 0

    while len(orders):
        item = orders.pop(0)

        if item == "(":
            q.append(item)
            num_unclosed_parens += 1
        elif item == ")":
            if num_unclosed_parens == 1:
                results.append(q + [")"])
                q = []
            else:
                q.append(item)
            num_unclosed_parens -= 1
        else:
            q.append(item)

    return results


async def read_data(loop, sock, self_power=""):
    # read message type and remaining length
    #data = await loop.sock_recv(sock, 4)
    try:
        data = await asyncio.wait_for(loop.sock_recv(sock, 4), timeout=5)
        hex_data = data.hex()
        message_type_hex, remaining_len_hex = hex_data[:4], hex_data[4:]

        message_type = int(message_type_hex[:2], 16)
        remaining_len = int(remaining_len_hex, 16)


        if remaining_len > 3999: # SUB
            logging.error("sub problem, exiting")
            sys.exit(1)

        # read remaining data
        rest = await loop.sock_recv(sock, remaining_len)

        if LOG:
            with open("log.txt", "a") as f:
                f.write(f"{self_power} -> s: {remaining_len} {" ".join(convert(rest.hex()))}\n")

        return message_type, rest.hex()
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("No data received")


def build_HLO(power, is_engine):
    """
    @param power: three letter power name
    """

    if not PRESS or is_engine:
        lvl = "0000"
    else:
        lvl = "1f40" 

    payload = convert_to_hex(
        [
            "HLO",
            "(",
            power,
            ")",
            "(",
            "0000",
            ")",
            "(",
            "(",
            "LVL",
            lvl,
            ")",
            ")",
        ]
    )

    pooled = hex(526)[2:].zfill(4) + hex(26)[2:].zfill(4) + payload

    return pooled


def build_FRM(power_abbr, sender, payload: List[str]):
    frm_prefix = [
        "FRM",
        "(",
        sender,
        ")",
        "(",
        power_abbr,
        ")",
        "(",
    ]

    frm_prefix.extend(payload)
    frm_prefix.append(")")

    frm_hex = convert_to_hex(frm_prefix)
    length = cal_remaining_len(frm_hex)

    return hex(526)[2:].zfill(4) + decimal_to_hex(length) + frm_hex


def build_SCO(game_state, self_power, friendly_power=None, hostile_power=None):
    """
    return a SCO string to be sent to albert
    """

    assert not (all([friendly_power, hostile_power])), (
        "Cannot have both friendly and hostile power"
    )

    centers_dict = game_state["state"]["centers"]

    sco_prefix = ["SCO"]

    for power, centers in centers_dict.items():
        power_abbr = POWERS_ABBRS[power]

        if friendly_power and power_abbr == friendly_power:
            power_abbr = self_power
        elif hostile_power and power_abbr != hostile_power:
            power_abbr = self_power

        to_append = ["(", power_abbr]

        to_append.extend(centers)
        to_append.append(")")

        sco_prefix.extend(to_append)

    unoccupied_centers = set(SUPPLY_CENTERS) - set(
        [x for y in centers_dict.values() for x in y]
    )

    sco_prefix.extend(["(", "UNO"])
    sco_prefix.extend(list(unoccupied_centers))
    sco_prefix.append(")")

    sco_hex = convert_to_hex(sco_prefix)
    length = cal_remaining_len(sco_hex)

    return hex(526)[2:].zfill(4) + decimal_to_hex(length) + sco_hex


def build_NOW(game, self_power, ally_powers=None):
    """
    return a tuple of (ORDs, NOW) to be sent to albert
    """

    # for calculating stance advice
    current_phase = game.get_phase_data()
         
    game_state = GamePhaseData.to_dict(current_phase)

    orders = build_ORD(game, self_power)
    ords = []

    phase = game_state["name"]
    daide_phase = None
    if phase[0] == "S" and phase[-1] == "M":
        daide_phase = "SPR"
    elif phase[0] == "S" and phase[-1] == "R":
        daide_phase = "SUM"
    elif phase[0] == "F" and phase[-1] == "M":
        daide_phase = "FAL"
    elif phase[0] == "F" and phase[-1] == "R":
        daide_phase = "AUT"
    elif phase[-1] == "A":
        daide_phase = "WIN"
    else:
        raise ValueError(f"Invalid phase {phase}")

    year = phase[1:5]
    assert year.isdigit(), f"Year must be a number, but got {year}"
    year = int(year)
    hex_year = decimal_to_hex(year)

    # send ORD first
    for order, result in orders:
        order_splitted = order.split(" ")
        ord_prefix = ["ORD", "(", daide_phase, hex_year, ")", "("]
        ord_prefix.extend(order_splitted)
        ord_prefix.extend([")", "(", result, ")"])
        ord_hex = convert_to_hex(ord_prefix)
        length = cal_remaining_len(ord_hex)
        ords.append(hex(526)[2:].zfill(4) + decimal_to_hex(length) + ord_hex)

    # calculate if need to include MRT
    need_mrt = False
    mrts = []
    if game_state["state"]["retreats"]:
        if any(len(x) for x in game_state["state"]["retreats"].values()) or any(
            x.startswith("*")
            for vs in game_state["state"]["units"].values()
            for x in vs
        ):
            need_mrt = True

    if need_mrt:
        mrts = build_MRT(game)

    now_prefix = ["NOW", "(", daide_phase, hex_year, ")"]

    for power, units in game_state["state"]["units"].items():
        power_abbr = POWERS_ABBRS[power]

        if ally_powers:
            if power in ally_powers:
                power_abbr = self_power

        for unit in units:
            # handle retreats
            if unit.startswith("*"):
                unit = unit[1:]
            unit_split = unit.split(" ")
            unit_hex = daidefy_unit(unit_split, game=None, power=power_abbr)

            # replace (POW TYP LOC) with (POW TYP LOC (MRT LOC))
            if need_mrt:
                for mrt in mrts:
                    if mrt[0] == unit_hex:
                        unit_hex = mrt[1]
                        break

            unit_splitted = unit_hex.split(" ")
            now_prefix.extend(unit_splitted)

    now_hex = convert_to_hex(now_prefix)
    length = cal_remaining_len(now_hex)

    return (ords, hex(526)[2:].zfill(4) + decimal_to_hex(length) + now_hex)


def build_ORD(game, power_abbr):
    current_phase = game.get_phase_data()
    game_state = GamePhaseData.to_dict(current_phase)

    albert_orders = game_state["orders"][POWER_NAMES[power_abbr]]
    results = game_state["results"]
    albert_units = game_state["state"]["units"][POWER_NAMES[power_abbr]]

    outputs = []

    for unit in albert_units:
        unit_result = results.get(unit)

        if unit_result is None:
            # logging.warning(f"Unit {unit} has no result")
            continue

        # TODO handle possible Paquette results: { 'disband'}
        if not len(unit_result) or not len(unit_result[0]):
            result_type = "SUC"
        elif unit_result[0] == "bounce":
            result_type = "BNC"
        elif unit_result[0] == "cut":
            result_type = "CUT"
        elif unit_result[0] == "dislodged":
            result_type = "DSR"
        elif unit_result[0] == "no convoy" or unit_result[0] == "void":
            result_type = "NSO"
        else:
            result_type = "SUC"  # Default fallback

        order = [x for x in albert_orders if x.startswith(unit)]
        if len(order) != 1:
            raise ValueError(
                f"Order not found for unit {unit}, orders: {albert_orders}"
            )
        daide_order = daidefy_order(game, POWER_NAMES[power_abbr], order[0])

        outputs.append((daide_order, result_type))

    return outputs


def build_MRT(game):
    current_phase = game.get_phase_data()
    game_state = GamePhaseData.to_dict(current_phase)
    assert game_state["name"].endswith(
        "R"
    ), f"Phase must be retreat phase, but got {game_state['name']}"
    possible_retreats = game_state["state"]["retreats"]

    results = []

    for power, retreat_dict in possible_retreats.items():
        power_abbr = POWERS_ABBRS[power]
        for unit, possible_retreat_locs in retreat_dict.items():
            daide_unit = daidefy_unit(unit.split(" "), game=None, power=power_abbr)
            retreat_locs = [daidefy_location(loc) for loc in possible_retreat_locs]

            mrts = " ".join(["MRT", "("] + retreat_locs + [")"]) + " )"
            # put mrts at the end of daide unit
            mrt_order = daide_unit[:-1] + mrts
            # return a tuple for indexing in NOW
            results.append((daide_unit, mrt_order))

    return results


async def send_response(client_socket, loop, response):
    await loop.sock_sendall(
        client_socket,
        response if isinstance(response, bytes) else bytes.fromhex(response),
    )


async def handle_game_active(client_socket, power_abbr, loop, game, is_engine):
    while game.status != "active":
        await asyncio.sleep(1)

    logging.info("Game is active")
    hlo_msg = build_HLO(power_abbr, is_engine)

    await loop.sock_sendall(
        client_socket,
        hlo_msg if isinstance(hlo_msg, bytes) else bytes.fromhex(hlo_msg),
    )


async def handle_game_completion(game):
    logging.info("Game completed")
    game_state = GamePhaseData.to_dict(game.get_phase_data())
    with open(f"{game_state['name']}.json", "w") as f:
        json.dump(game_state, f)


def create_da10_response():
    return bytes.fromhex(hex(256)[2:].zfill(4) + hex(0)[2:].zfill(4))


async def handle_initialization(client_socket, loop):
    initialization_done = False

    while not initialization_done:
        message_type, data = await read_data(loop, client_socket)

        if data:
            payload = " ".join(convert(data))

            if "da10" in payload:
                response = create_da10_response()

                await loop.sock_sendall(
                    client_socket,
                    response if isinstance(response, bytes) else bytes.fromhex(response),
                )

            elif "NME" in payload:
                yes_response_prefix = convert_to_hex(["YES", "("])
                yes_response_suffix = convert_to_hex([")"])

                remaining_len = cal_remaining_len(
                    yes_response_prefix + data + yes_response_suffix
                )

                pooled = (
                    hex(524)[2:].zfill(4)
                    + decimal_to_hex(remaining_len)
                    + yes_response_prefix
                    + data
                    + yes_response_suffix
                )
                await loop.sock_sendall(
                    client_socket,
                    pooled if isinstance(pooled, bytes) else bytes.fromhex(pooled),
                )

                # send map definitions
                map_def_prefix = convert_to_hex(["MAP", "("])
                map_name = "STANDARD"
                map_name_hex = [hex(19200 + ord(x))[2:].zfill(4) for x in map_name]
                map_def_suffix = convert_to_hex([")"])

                pooled = (
                    hex(589)[2:].zfill(4)
                    + hex(22)[2:].zfill(4)
                    + map_def_prefix
                    + "".join(map_name_hex)
                    + map_def_suffix
                )
                await loop.sock_sendall(
                    client_socket,
                    pooled if isinstance(pooled, bytes) else bytes.fromhex(pooled),
                )
            elif "MDF" in payload:
                prefix = hex(525)[2:].zfill(4) + hex(2562)[2:].zfill(4)
                map_definition = MAPDEF
                map_def_hex = convert_to_hex(map_definition)

                await loop.sock_sendall(
                    client_socket,
                    prefix + map_def_hex if isinstance(prefix + map_def_hex, bytes) else bytes.fromhex(prefix + map_def_hex),
                )

                initialization_done = True


aggregated_orders = {}
orders_lock = asyncio.Lock()
game_instance = None
current_game_phase = None
orderable_powers = []
waiting_for_orders = True

async def submit_aggregated_orders():
    global aggregated_orders, current_game_phase, orderable_powers, waiting_for_orders

    while True:
        # Check for phase change or a set interval
        await asyncio.sleep(2) # Check every 2 seconds, adjust as needed

        if game_instance:
            phase_data = game_instance.get_phase_data()
            game_state = GamePhaseData.to_dict(phase_data)
            new_phase = game_state["name"]
            orderable_powers = [k for k, v in game_instance.get_orderable_locations().items() if len(v) > 0]

            if new_phase != current_game_phase:
                # Reset aggregated orders for the new phase
                async with orders_lock:
                    aggregated_orders = {}
                    waiting_for_orders = True

                current_game_phase = new_phase

            if waiting_for_orders and len(aggregated_orders) == len(orderable_powers):
                async with orders_lock:
                    for power, orders_list in aggregated_orders.items():
                        print(f"orders for {power}: {orders_list}")

                current_game_phase = new_phase
                orderable_powers = []
                waiting_for_orders = False

            print(f"Aggregated orders for {current_game_phase}: {aggregated_orders}")
            print(orderable_powers)
            print(new_phase, current_game_phase, waiting_for_orders)


async def handle_client(client_socket, client_address, power, is_engine):
    global game_instance, current_game_phase, aggregated_orders, waiting_for_orders

    # connect to paquette
    connection = await connect(HOSTNAME, PORT, USE_SSL)

    credentials = (
        f"cicero_{power}",
        "password",
    )
    admin_credentials = (
        f"ADMIN_{power}",
        "password",
    )

    if is_engine:
        channel = await connection.authenticate(*credentials)
        game: NetworkGame = await channel.join_game(
            game_id=GAME_ID, power_name=power
        )
    else:
        channel = await connection.authenticate(*admin_credentials)
        game: NetworkGame = await channel.join_game(
            game_id=GAME_ID
        )

    if game_instance is None:
        game_instance = game
        phase_data = game.get_phase_data()
        current_game_phase = GamePhaseData.to_dict(phase_data)["name"]
        # Initialize aggregated_orders for all powers


    logging.info(f"Connection established with {client_address}")
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    logging.info(f"SO_KEEPALIVE set for {client_address}")
    loop = asyncio.get_running_loop()

    current_phase = None

    # Handle client interaction
    await handle_initialization(client_socket, loop)  # wait for Albert ready
    await handle_game_active(
        client_socket, POWERS_ABBRS[power], loop, game, is_engine
    )  # wait for Paquette game ready

    logging.info("Initialization done, proceeding to game after 3 seconds")
    send_SCO = True
    send_NOW = False

    prev_power_stance = None # list of allies

    orderable_units = {}
    messages_sent = []

    while True:
        paquette_game = game.get_phase_data()
        game_state = GamePhaseData.to_dict(paquette_game)

        # read data from client socket
        try:
            message_type, data = await read_data(loop, client_socket, power)

            if data:
                converted = convert(data)
                payload = " ".join(converted)

                if "GOF" in payload or "DRW" in payload or "SND" in payload:
                    yes_response_prefix = convert_to_hex(["YES", "("])
                    yes_response_suffix = convert_to_hex([")"])

                    remaining_len = cal_remaining_len(
                        yes_response_prefix + data + yes_response_suffix
                    )

                    pooled = (
                        hex(526)[2:].zfill(4)
                        + decimal_to_hex(remaining_len)
                        + yes_response_prefix
                        + data
                        + yes_response_suffix
                    )

                    await loop.sock_sendall(
                        client_socket,
                        pooled if isinstance(pooled, bytes) else bytes.fromhex(pooled),
                    )

                    if "SND" in payload:
                        assert PRESS and not is_engine, "Press is not enabled"

                        if any(
                            x in converted
                            for x in ["WIN", "AUT", "SUM", "SPR", "FAL"]
                        ):
                            msg = converted[5:]
                        else:
                            msg = converted[1:]

                        msg = tokenize(msg)
                        assert (
                            len(msg) == 2
                        ), f"Msg should contain recipient and message, but got {msg}"
                        recipients = msg[0][1:-1]  # removes parentheses
                        message = msg[1][1:-1]  # removes parentheses
                        daide = " ".join(message)
                        prp_response = None
                        if "REJ" in message:
                            prp_response = "no"
                        if "YES" in message:
                            prp_response = "yes"

                        if USE_NL:
                            if prp_response is None:
                                message = gen_english(daide)
                            else:
                                message = prp_response
                        else:
                            message = daide

                        for recipient in recipients:
                            try:
                                await send_game_message(game, 
                                    Message(
                                        sender=power,
                                        recipient=POWER_NAMES[recipient],
                                        message=message,
                                        phase=current_phase,
                                        type="daide",
                                        daide=daide
                                    )                    
                                                        
                                    #) game.send_game_message(
                                    #message=
                                )
                            except Exception:
                                phase_data = game.get_phase_data()
                                game_state = GamePhaseData.to_dict(phase_data)
                                new_phase = game_state["name"]

                                logging.warning(f"Error sending: {message}, resending with {new_phase}...")
                                
                                await send_game_message(game, Message(
                                        sender=power,
                                        recipient=POWER_NAMES[recipient],
                                        message=message,
                                        phase=current_phase,
                                        type="daide",
                                        daide=daide
                                    )) 
                            finally:
                                with open("msg.txt", "a") as f:
                                    f.write(f"{power} -> {recipient}: {message}\n")

                    elif "GOF" in payload:
                        if "NOT" not in payload:
                            if is_engine and not game_state["name"].endswith("M"):
                                await game.no_wait()
                        elif is_engine and "NOT" in payload:
                            await game.wait()
                    elif "DRW" in payload:
                        if "NOT" not in payload:
                            await game.vote(vote='yes')

                elif "SUB" in payload:
                    to_submit = []

                    if any(
                        x in converted for x in ["WIN", "AUT", "SUM", "SPR", "FAL"]
                    ):
                        orders = converted[5:]
                    else:
                        orders = converted[1:]
                    orders = tokenize(orders)

                    response_prefix = convert_to_hex(["THX", "("])
                    response_suffix = convert_to_hex([")", "(", "MBV", ")"])

                    for order in orders:
                        response = (
                            response_prefix
                            + convert_to_hex(order)
                            + response_suffix
                        )
                        remaining_len = cal_remaining_len(response)

                        pooled = (
                            hex(598)[2:].zfill(4)
                            + decimal_to_hex(remaining_len)
                            + response
                        )

                        await loop.sock_sendall(
                            client_socket,
                            pooled if isinstance(pooled, bytes) else bytes.fromhex(pooled),
                        )

                        parsed = " ".join(order[1:-1])  # remove parentheses
                        dipnet_o = dipnet_order(parsed)

                        if dipnet_o != "WAIVE":
                            to_submit.append(dipnet_o)

                        async with orders_lock:
                            aggregated_orders[power] = to_submit


                    if is_engine:
                        try:
                            await set_game_orders(game, to_submit) #game.set_orders(orders=to_submit)
                        except Exception:
                            phase_data = game.get_phase_data()
                            game_state = GamePhaseData.to_dict(phase_data)
                            new_phase = game_state["name"]

                            logging.warning(f"Error submitting orders, resubmitting with {new_phase}...")

                            await set_game_orders(game, to_submit) #game.set_orders(orders=to_submit)

        # if no data is received, send game info to socket
        except asyncio.TimeoutError:
            if game_state["name"] == "COMPLETED" or game.status == "completed":
                await handle_game_completion(game)
                exit(0)

            # send SCO on new year, and ORD/NOW on new phase
            if current_phase != game_state["name"]:
                #if (is_advisor and advisor) and not game_state["name"].endswith("M"):
                    # if is advisor and not movement phase, skip
                    #continue

                current_phase = game_state["name"]
                logging.info(f"Advance to {current_phase}")

                orderable_units = game_state["state"]["units"]
                orderable_locations = game.get_orderable_locations()

                # check if game completed
                if game_state["name"] == "COMPLETED":
                    await handle_game_completion(game)
                    sys.exit(0)

                if current_phase.endswith("A"):
                    send_SCO = True
                #if not is_advisor or not advisor:
                send_NOW = True

            if send_SCO:
                sco = build_SCO(game_state, POWERS_ABBRS[power])
                await loop.sock_sendall(
                    client_socket,
                    sco if isinstance(sco, bytes) else bytes.fromhex(sco),
                )
                send_SCO = False

            if send_NOW:
                ally_powers_initial = [k for k, v in prev_power_stance.items() if v > 0] if prev_power_stance else None
                ords, now = build_NOW(game, POWERS_ABBRS[power], ally_powers=ally_powers_initial)
                for oo in ords:
                    await loop.sock_sendall(
                        client_socket,
                        oo if isinstance(oo, bytes) else bytes.fromhex(oo),
                    )
                await loop.sock_sendall(
                    client_socket,
                    now if isinstance(now, bytes) else bytes.fromhex(now),
                )

                send_NOW = False

            if PRESS and not is_engine:
                # update messages to Albert
                to_albert = [
                    x
                    for x in game_state["messages"]
                    if x["time_sent"] not in messages_sent and x["recipient"] == power and x["phase"] == game_state["name"]
                ]
                messages_sent.extend([x["time_sent"] for x in to_albert])

                for message in to_albert:
                    if "daide" in message and message["daide"]:
                        message_payload = message["daide"]
                        sender = message["sender"]
                        sender = POWERS_ABBRS[sender]

                        to_send = []

                        payload = sanitize_daide(message_payload, to_send)
                    
                        if is_valid_daide_message(message_payload) and not any(x not in DAIDE2HEX.keys() for x in payload):
                            frm = build_FRM(POWERS_ABBRS[power], sender, payload)

                            logging.info(f"Sending message to Albert: {" ".join(convert(frm))}")
                            await loop.sock_sendall(
                                client_socket,
                                frm if isinstance(frm, bytes) else bytes.fromhex(frm),
                            )

        await asyncio.sleep(1)


async def run():
    # websocket
    server_host = "0.0.0.0"  # Listen on all available interfaces
    server_port = 16713

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_host, server_port))
    server_socket.listen(7)  # Allow up to 7 queued connections
    logging.info(f"Server listening on {server_host}:{server_port}")

    # server_socket.setblocking(False)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_global_exceptions)

    create_task_with_exception_handling(
        submit_aggregated_orders(),
        task_name="Order Aggregation and Submission Task"
    )


    try:
        while True:
            # Accept connections asynchronously
            client_socket, client_address = await loop.run_in_executor(
                None, server_socket.accept
            )

            if not power_queues["TO_ENGINE"].empty():
                assigned_power = (power_queues["TO_ENGINE"].get(), True)
            elif not power_queues["NOT_ASSIGNED"].empty():
                assigned_power = (power_queues["NOT_ASSIGNED"].get(), False)
            else:
                raise RuntimeError("No available power to assign to client")
            
            # Handle the client in an async function
            create_task_with_exception_handling(
                handle_socket_client(client_socket, client_address, assigned_power[0], assigned_power[1]),
                task_name=f"Handle client {client_address}",
            )
    except KeyboardInterrupt:
        logging.error("Server shutting down...")
    finally:
        server_socket.close()


async def handle_socket_client(client_socket, client_address, power, is_engine):
    try:
        logging.info(f"Handling client {client_address}")
        await handle_client(client_socket, client_address, power, is_engine)
    except Exception as e:
        logging.error(f"Error handling client {power} {client_address}: {e}")
        traceback.print_exc()
    finally:
        client_socket.close()


def create_task_with_exception_handling(coro, task_name="Unnamed Task"):
    """
    Wraps asyncio.create_task to add exception handling.
    """

    async def task_wrapper():
        try:
            await coro
        except Exception as e:
            logging.error(f"Exception in {task_name}: {e}")
            traceback.print_exc()

    return asyncio.create_task(task_wrapper(), name=task_name)


def handle_global_exceptions(loop, context):
    """
    Handles exceptions caught by the event loop.
    """
    msg = context.get("exception", context["message"])
    logging.info(f"Caught global exception: {msg}")
    traceback.print_exc()


if __name__ == "__main__":
    if os.path.exists("./log.txt"):
        os.remove("./log.txt")

    asyncio.run(run())
