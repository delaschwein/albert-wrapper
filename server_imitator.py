from utils import (
    convert,
    convert_to_hex,
    POWER_NAMES,
    decimal_to_hex,
    daidefy_order,
    cal_remaining_len,
    daidefy_unit,
    dipnet_order,
    daidefy_location,
)
import socket
import json
from time import sleep
from diplomacy.utils.game_phase_data import GamePhaseData
from diplomacy.client.network_game import NetworkGame
from diplomacy.client.connection import connect
import asyncio
from chiron_utils.bots.baseline_bot import BaselineBot, BotType
from abc import ABC
from typing import List, Sequence
import os
from diplomacy.utils.constants import SuggestionType


# @TODO: implement press


POWERS_ABBRS = {v: k for k, v in POWER_NAMES.items()}
LOG = True
DESIGNATED_ALBERT_POWER_ABBR = "AUS"
HOSTNAME = "localhost"
HOST_PORT = 8433
GAME_ID = "test"
IS_ADVISOR = True


with open("mapdef.json", "r") as f:
    MAPDEF = json.load(f)

with open("scs.json", "r") as f:
    SUPPLY_CENTERS = json.load(f)


"""
    NOTE: as long as DM prefix is >= 512 && < 768 it is valid
"""

class AlbertBot(BaselineBot, ABC):
    async def gen_orders(self) -> List[str]:
        return []

    async def do_messaging_round(self, orders: Sequence[str]) -> List[str]:
        return []


class AlbertAdvisor(AlbertBot):
    """Advisor form of `CiceroBot`."""

    bot_type = BotType.ADVISOR
    suggestion_type = SuggestionType.MOVE


def tokenize_orders(orders):
    """
    convert a list of orders e.g.,["(", "(", "AUS", "AMY", "BUD", ")", "MTO", "VIE", ")"] to a list of lists e.g., [["(", "(", "AUS", "AMY", "BUD", ")", "MTO", "VIE", ")"]]
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


async def read_data(loop, sock):
    # read message type and remaining length
    data = await loop.sock_recv(sock, 4)
    hex_data = data.hex()
    message_type_hex, remaining_len_hex = hex_data[:4], hex_data[4:]

    message_type = int(message_type_hex[:2], 16)
    remaining_len = int(remaining_len_hex, 16)

    # read remaining data
    rest = await loop.sock_recv(sock, remaining_len)

    if LOG:
        with open("log.txt", "a") as f:
            f.write(f"c -> s: {" ".join(convert(rest.hex()))}\n")

    return message_type, rest.hex()


def build_HLO(power):
    """
    @param power: three letter power name
    """
    payload = convert_to_hex(
        ["HLO", "(", power, ")", "(", "0000", ")", "(", "(", "LVL", "0000", ")", ")"]
    )

    pooled = hex(526)[2:].zfill(4) + hex(26)[2:].zfill(4) + payload

    # client_socket.sendall(bytes.fromhex(pooled))
    return pooled


def build_SCO(game_state):
    """
    return a SCO string to be sent to albert
    """

    centers_dict = game_state["state"]["centers"]

    sco_prefix = ["SCO"]

    for power, centers in centers_dict.items():
        power_abbr = POWERS_ABBRS[power]
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


def build_NOW(game):
    """
    return a tuple of (ORDs, NOW) to be sent to albert
    """

    current_phase = game.get_phase_data()
    game_state = GamePhaseData.to_dict(current_phase)

    orders = build_ORD(game)
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


def build_ORD(game):
    current_phase = game.get_phase_data()
    game_state = GamePhaseData.to_dict(current_phase)

    albert_orders = game_state["orders"][POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR]]
    results = game_state["results"]
    # pprint(game_state)
    albert_units = game_state["state"]["units"][
        POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR]
    ]

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

        order = [x for x in albert_orders if x.startswith(unit)]
        if len(order) != 1:
            raise ValueError(
                f"Order not found for unit {unit}, orders: {albert_orders}"
            )
        daide_order = daidefy_order(
            game, POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR], order[0]
        )

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


async def handle_client(client_socket, client_address, game, advisor=None):
    print(f"Connection established with {client_address}")
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    print(f"SO_KEEPALIVE set for {client_address}")
    loop = asyncio.get_running_loop()

    initialization_done = False
    game_active = False
    current_phase = None

    # Handle client interaction
    try:
        while not initialization_done:
            message_type, data = await read_data(loop, client_socket)
            # data = client_socket.recv(1024)
            if data:
                payload = " ".join(convert(data))
                # print(payload)

                if "da10" in payload:
                    response = hex(256)[2:].zfill(4) + hex(0)[2:].zfill(4)
                    response = bytes.fromhex(response)
                    # print(f"Sending response for magic num: {response.hex()}")
                    await loop.sock_sendall(client_socket, response)

                    if LOG:
                        with open("log.txt", "a") as f:
                            f.write(f"s -> c: {" ".join(convert(response.hex()))}\n")

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

                    if LOG:
                        with open("log.txt", "a") as f:
                            f.write(
                                f"s -> c: {" ".join(convert(yes_response_prefix + data + yes_response_suffix))}\n"
                            )
                    await loop.sock_sendall(client_socket, bytes.fromhex(pooled))
                    # print(f"sent {" ".join(convert(pooled))}")

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

                    if LOG:
                        with open("log.txt", "a") as f:
                            f.write(
                                f"s -> c: {" ".join(convert(map_def_prefix + "".join(map_name_hex) + map_def_suffix))}...\n"
                            )

                    await loop.sock_sendall(client_socket, bytes.fromhex(pooled))
                    # print(f"sent {" ".join(convert(pooled))}")
                elif "MDF" in payload:
                    prefix = hex(525)[2:].zfill(4) + hex(2562)[2:].zfill(4)
                    map_definition = MAPDEF
                    map_def_hex = convert_to_hex(map_definition)

                    if LOG:
                        with open("log.txt", "a") as f:
                            f.write("s -> c: MDF...\n")

                    await loop.sock_sendall(
                        client_socket, bytes.fromhex(prefix + map_def_hex)
                    )
                    # print(f"sent {" ".join(convert(prefix + map_def_hex))}")

                    initialization_done = True
                    break

        while not game_active:
            if game.status == "active":
                game_active = True
                break

            sleep(1)

        print("Game is active")
        hlo_msg = build_HLO(DESIGNATED_ALBERT_POWER_ABBR)
        await loop.sock_sendall(client_socket, bytes.fromhex(hlo_msg))
        if LOG:
            with open("log.txt", "a") as f:
                f.write(f"s -> c: {" ".join(convert(hlo_msg))}\n")

        if initialization_done:
            print("Initialization done, proceeding to game after 5 seconds")
            sleep(5)
            send_SCO = True
            send_NOW = False

            while True:
                try:
                    message_type, data = await asyncio.wait_for(
                        read_data(loop, client_socket), timeout=5
                    )

                    if data:
                        converted = convert(data)
                        payload = " ".join(converted)

                        if "GOF" in payload or "DRW" in payload:
                            yes_response_prefix = convert_to_hex(["YES", "("])
                            yes_response_suffix = convert_to_hex([")"])

                            remaining_len = 0

                            if "NOT" in payload:
                                remaining_len = hex(14)[2:].zfill(4)
                            else:
                                remaining_len = hex(8)[2:].zfill(4)

                            pooled = (
                                hex(526)[2:].zfill(4)
                                + remaining_len
                                + yes_response_prefix
                                + data
                                + yes_response_suffix
                            )

                            await loop.sock_sendall(
                                client_socket, bytes.fromhex(pooled)
                            )

                            if LOG:
                                with open("log.txt", "a") as f:
                                    f.write(
                                        f"s -> c: {" ".join(convert(yes_response_prefix + data + yes_response_suffix))}\n"
                                    )

                        elif "SUB" in payload:
                            to_submit = []
                            if any(x in converted for x in ["WIN", "AUT", "SUM", "SPR", "FAL"]):
                                orders = converted[5:]
                            else:
                                orders = converted[1:]
                            orders = tokenize_orders(orders)

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
                                    client_socket, bytes.fromhex(pooled)
                                )

                                if LOG:
                                    with open("log.txt", "a") as f:
                                        f.write(
                                            f"s -> c: {" ".join(convert(response))}\n"
                                        )

                                parsed = " ".join(order[1:-1])  # remove parentheses
                                dipnet_o = dipnet_order(parsed)
                                to_submit.append(dipnet_o)

                            
                            if IS_ADVISOR and advisor:
                                await advisor.declare_suggestion_type()
                                await advisor.suggest_orders(to_submit)

                            else:
                                print(f"Submitting orders: {to_submit}")
                                await game.set_orders(orders=to_submit)


                            # game.process()

                except asyncio.TimeoutError:
                    if game.status == "completed":
                        print("Game completed")
                        print(GamePhaseData.to_dict(game.get_phase_data()))
                        exit(0)

                    paquette_game = game.get_phase_data()
                    game_state = GamePhaseData.to_dict(paquette_game)

                    # send SCO on new year, and ORD/NOW on new phase
                    if current_phase != game_state["name"]:
                        current_phase = game_state["name"]
                        print(f"Advance to {current_phase}")

                        # if current_phase[1:5] != current_year:
                        #    current_year = current_phase[1:5]

                        if current_phase.endswith("A"):
                            send_SCO = True
                        send_NOW = True

                    if send_SCO:
                        sco = build_SCO(game_state)
                        await loop.sock_sendall(client_socket, bytes.fromhex(sco))
                        if LOG:
                            with open("log.txt", "a") as f:
                                f.write(f"s -> c: {" ".join(convert(sco))}\n")
                        send_SCO = False

                    if send_NOW:
                        ords, now = build_NOW(game)
                        for oo in ords:
                            await loop.sock_sendall(client_socket, bytes.fromhex(oo))
                            if LOG:
                                with open("log.txt", "a") as f:
                                    f.write(f"s -> c: {" ".join(convert(oo))}\n")
                        await loop.sock_sendall(client_socket, bytes.fromhex(now))
                        if LOG:
                            with open("log.txt", "a") as f:
                                f.write(f"s -> c: {" ".join(convert(now))}\n")
                        send_NOW = False
                asyncio.sleep(1)

    except Exception as e:
        print(f"Error with client {client_address}: {e}")
    finally:
        print(f"Closing connection with {client_address}")
        client_socket.close()


async def run():
    # Paquette
    connection = await connect(HOSTNAME, HOST_PORT, False)
    
    

    if IS_ADVISOR:
        credentials = ("admin", "password")
        channel = await connection.authenticate(*credentials)
        game: NetworkGame = await channel.join_game(game_id="test")
        advisor = AlbertAdvisor(POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR], game)
    else:
        credentials = (f"cicero_{POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR]}", "password")
        channel = await connection.authenticate(*credentials)
        game: NetworkGame = await channel.join_game(
            game_id="test", power_name=POWER_NAMES[DESIGNATED_ALBERT_POWER_ABBR]
        )
        

    # websocket
    server_host = "0.0.0.0"  # Listen on all available interfaces
    server_port = 16713

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)  # Allow up to 5 queued connections
    print(f"Server listening on {server_host}:{server_port}")

    # server_socket.setblocking(False)
    loop = asyncio.get_running_loop()

    try:
        while True:
            # Accept connections asynchronously
            client_socket, client_address = await loop.run_in_executor(
                None, server_socket.accept
            )
            print(f"New connection from {client_address}")
            # Handle the client in an async function
            if IS_ADVISOR:
                await asyncio.create_task(
                    handle_socket_client(client_socket, client_address, game, advisor)
                )
            else:
                await asyncio.create_task(
                    handle_socket_client(client_socket, client_address, game)
                )
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()

    """ try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            client_handler = threading.Thread(
                target=handle_client, args=(client_socket, client_address, game)
            )
            client_handler.daemon = (
                True  # Allow program to exit even if thread is running
            )
            client_handler.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close() """


async def handle_socket_client(client_socket, client_address, game, advisor=None):
    try:
        # You can now integrate this with your existing game logic
        print(f"Handling client {client_address}")
        if advisor:
            await handle_client(
                client_socket, client_address, game, advisor
            )
        else:
            await handle_client(
                client_socket, client_address, game
            )  # Assuming it handles socket interaction
    finally:
        client_socket.close()


if __name__ == "__main__":
    # if log.txt exists, delete it
    if os.path.exists("./log.txt"):
        os.remove("./log.txt")

    asyncio.run(run())
