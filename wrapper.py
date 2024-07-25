import socket
import random
from typing_extensions import List

from utils import (
    convert,
    convert_to_hex,
    POWER_NAMES,
    DIPNET2DAIDE_LOC,
    DAIDE2DIPNET_LOC,
    dipnet_location,
    daidefy_location,
    dipnet_unit,
    daidefy_unit,
    get_unit_power,
    decimal_to_hex,
    dipnet_order,
    daidefy_order,
    cal_remaining_len,
    hex_to_decimal,
)
from diplomacy import Game

game = Game()


"""
order types
( POW UNT LOC ) HLD <--> U LOC H
( POW UNT LOC ) MTO LOC <--> U LOC - LOC
( POW UNT LOC ) SUP ( POW UNT LOC ) <--> U LOC S U LOC H
( POW UNT LOC ) SUP ( POW UNT LOC ) MTO PNC <--> U LOC S U LOC - LOC
( POW UNT LOC ) CVY ( POW UNT LOC ) CTO LOC <--> U LOC C U LOC - LOC
( POW UNT LOC ) CTO ( POW UNT LOC ) VIA (LOC ...) <--> U LOC - LOC VIA

( POW UNT LOC ) DSB <--> U LOC D
( POW UNT LOC ) RTO LOC <--> U LOC R LOC
( POW UNT LOC ) BLD <--> U LOC B
( POW UNT LOC ) REM <--> U LOC D
POW WVE <--> ?

"""


def main():
    def read_data(sock):
        # read message type and remaining length
        data = sock.recv(4)
        hex_data = data.hex()
        message_type_hex, remaining_len_hex = hex_data[:4], hex_data[4:]

        message_type = int(message_type_hex[:2], 16)
        remaining_len = int(remaining_len_hex, 16)

        # read remaining data
        rest = sock.recv(remaining_len)
        return message_type, rest.hex()

    def send_order(sock, order):
        # set wait
        not_gof = convert_to_hex(["NOT", "(", "GOF", ")"])
        len_not_gof = decimal_to_hex(cal_remaining_len(not_gof))

        sock.sendall(bytes.fromhex(DM_PREFIX + len_not_gof + not_gof))

        message_type, rest = read_data(sock)
        print(message_type, " ".join(convert(rest)))

        # generate, convert from shorthand to daide, send
        possible_orders = game.get_all_possible_orders()
        power_orders = [
            random.choice(possible_orders[loc])
            for loc in game.get_orderable_locations(POWER_NAMES[self_power])
            if possible_orders[loc]
        ]
        phase = game.phase
        year = phase.split(" ")[1]
        season = phase.split(" ")[0][:3]
        year_hex = decimal_to_hex(int(year))

        print("Converting:", power_orders)
        daide_orders = [
            daidefy_order(game, self_power, order) for order in power_orders
        ]
        print("Converted:", daide_orders)

        submit_orders = convert_to_hex(["SUB", "(", season, year_hex, ")"])

        for daide_order in daide_orders:
            pieces = daide_order.split(" ")
            submit_orders += convert_to_hex(["("])
            submit_orders += convert_to_hex(pieces)
            submit_orders += convert_to_hex([")"])

        sock.sendall(
            bytes.fromhex(
                DM_PREFIX
                + decimal_to_hex(cal_remaining_len(submit_orders))
                + submit_orders
            )
        )

        message_type, rest = read_data(sock)
        print(message_type, " ".join(convert(rest)))

        gof = convert_to_hex(["GOF"])

        sock.sendall(
            bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(gof)) + gof)
        )

        message_type, rest = read_data(sock)
        print(message_type, " ".join(convert(rest)))

    server_address = ("localhost", 16713)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Connect to the server
    sock.connect(server_address)
    print(f"Connected to {server_address}")

    message = "000000040001da10"

    nme_msg = "0200001c480c40004b424b6f4b74400140004b764b364b2e4b304b2e4b314001"

    mdf_msg = "02f40002480a"

    yes_map_standard = (
        "0200001c481c4000480940004b534b544b414b4e4b444b414b524b4440014001"
    )

    to_send = [message, nme_msg, mdf_msg, yes_map_standard]

    POWERS = ["AUS", "ENG", "FRA", "GER", "ITA", "RUS", "TUR"]

    DM_PREFIX = "0200"

    self_power = None

    try:
        for msg in to_send:
            # convert message to bytes
            msg = bytes.fromhex(msg)

            # Send data
            sock.sendall(msg)

            return_msg_type, return_data = read_data(sock)

        while True:
            return_msg_type, return_data = read_data(sock)

            daide = " ".join(convert(return_data))

            if any(power in daide for power in POWERS):
                print("assigned power:", daide[6:9])
                self_power = daide[6:9]

            if return_data == "4810" and daide == "OFF":
                # exit
                print("OFF message received, exiting...")
                break

            if self_power:
                send_order(sock, [])
                break

    except KeyboardInterrupt:
        print("Closing socket")
        sock.close()


if __name__ == "__main__":
    main()
