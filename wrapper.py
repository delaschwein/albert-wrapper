import socket
import random
import json

from utils import (
    convert,
    convert_to_hex,
    POWER_NAMES,
    decimal_to_hex,
    dipnet_order,
    daidefy_order,
    cal_remaining_len,
    hex_to_decimal,
    process_now,
    process_ord,
    dipnet_unit,
    process_sco,
)

from diplomacy import Game

game = Game()
game.add_rule("DONT_SKIP_PHASES")


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

    def send_not_gof(sock):
        # set wait
        not_gof = convert_to_hex(["NOT", "(", "GOF", ")"])
        len_not_gof = decimal_to_hex(cal_remaining_len(not_gof))

        sock.sendall(bytes.fromhex(DM_PREFIX + len_not_gof + not_gof))

        message_type, rest = read_data(sock)

    def send_gof(sock):
        gof = convert_to_hex(["GOF"])

        sock.sendall(
            bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(gof)) + gof)
        )

        message_type, rest = read_data(sock)

    def send_order(sock, orders):
        # only submit orders if there are any
        if len(orders) > 0:
            submit_orders = convert_to_hex(["SUB", "(", season, year_hex, ")"])

            for daide_order in orders:
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

    def get_random_orders():
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

        daide_orders = []

        for order in power_orders:
            cvy_loc = []

            if "VIA" in order:
                without_via = order.split("VIA")[0].strip()
                cvy_pattern = "C " + without_via

                # getting VIA locations
                for loc, loc_ords in possible_orders.items():
                    for loc_ord in loc_ords:
                        if cvy_pattern in loc_ord:
                            cvy_loc.append(loc_ord.split(" ")[1])
                            break

            # determine DSB or REM
            if game.get_current_phase()[-1] == "R":
                daide_orders.append(
                    daidefy_order(game, self_power, order, cvy_loc, True)
                )
            else:
                daide_orders.append(daidefy_order(game, self_power, order, cvy_loc))

        return daide_orders, season, year_hex

    def gen_send_orders(sock):
        """
        Generate random orders and send them to the server until success
        """
        ords, s, y = get_random_orders()

        success = False

        if len(ords) > 0:
            while not success:
                ords, s, y = get_random_orders()
                responses = []
                send_order(sock, ords)
                print(f"Sending orders: {ords}")

                for ii in range(len(ords)):
                    return_msg_type, return_data = read_data(sock)
                    response = " ".join(convert(return_data))
                    responses.append(response)

                if not any("NSU" in response for response in responses):
                    success = True
        return success

    server_address = ("localhost", 16713)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    sock.connect(server_address)

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
    curr_result = {}

    try:
        # join game
        for msg in to_send:
            # convert message to bytes
            msg = bytes.fromhex(msg)

            # Send data
            sock.sendall(msg)

            return_msg_type, return_data = read_data(sock)

        while True:
            return_msg_type, return_data = read_data(sock)

            daide = " ".join(convert(return_data))
            print(daide)

            if "MIS" in daide and self_power:
                pass

            if "HLO" in daide and any(power in daide for power in POWERS):
                self_power = daide[6:9]

            if return_data == "4810" and daide == "OFF":
                break

            if "SCO" in daide:
                dist = process_sco(daide.strip())
                game.clear_centers()
                for power, centers in dist.items():
                    game.set_centers(power, centers)

            if "NOW" in daide:
                curr_result = {}
                info = process_now(daide.strip())
                phase, *units = info
                season, year_hex = phase.split(" ")
                year = str(hex_to_decimal(year_hex))
                curr_phase = ""

                # ensure engine in sync
                if season == "SPR":
                    curr_phase = "S" + year + "M"
                elif season == "SUM":
                    curr_phase = "S" + year + "R"
                elif season == "FAL":
                    curr_phase = "F" + year + "M"
                elif season == "AUT":
                    curr_phase = "F" + year + "R"
                elif season == "WIN":
                    curr_phase = "W" + year + "A"

                game.set_current_phase(curr_phase)
                game.clear_units()

                unit_dict = {}

                for unit in units:
                    pow = unit[0:3]
                    sp = unit.split(" ")
                    if "MRT" in sp:
                        idx = sp.index("MRT")
                        sp = sp[:idx]
                    dipnet_u = dipnet_unit(["("] + sp + [")"])
                    if POWER_NAMES[pow] not in unit_dict:
                        unit_dict[POWER_NAMES[pow]] = []
                    unit_dict[POWER_NAMES[pow]].append(dipnet_u)

                for power, units in unit_dict.items():
                    game.set_units(power, units)

                print("result:", game.result)
                print("game state:", game.get_state())

                # send orders if power assigned
                if self_power:
                    send_not_gof(sock)
                    gen_send_orders(sock)
                    send_gof(sock)

            if "ORD" in daide:
                order_power = None
                phase, order, *rest = process_ord(daide.strip())

                season, year_hex = phase.split(" ")
                year = hex_to_decimal(year_hex)

                # receive order result from server and submit to local
                for token in order.split(" "):
                    if token in POWER_NAMES:
                        order_power = token
                        break

                order = dipnet_order(order)

                if order_power not in curr_result:
                    curr_result[order_power] = []
                curr_result[order_power].append(order)

                game.set_orders(POWER_NAMES[order_power], curr_result[order_power])

    except KeyboardInterrupt:
        print("Closing socket")
        sock.close()


if __name__ == "__main__":
    main()
