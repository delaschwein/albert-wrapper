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
    process_now,
    process_ord,
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
        print(message_type, " ".join(convert(rest)))

    def send_gof(sock):
        gof = convert_to_hex(["GOF"])

        sock.sendall(
            bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(gof)) + gof)
        )

        message_type, rest = read_data(sock)
        print(message_type, " ".join(convert(rest)))

    def send_order(sock, orders):
        #send_not_gof(sock)

        #daide_orders, season, year_hex = get_random_orders()

        

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

            #message_type, rest = read_data(sock)
            #print(message_type, " ".join(convert(rest)))

    def get_random_orders():
        # generate, convert from shorthand to daide, send
        print(f'generating random orders for {game.phase}')
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
                
                for ii in range(len(ords)):
                    return_msg_type, return_data = read_data(sock)
                    print(f'order submit result: {" ".join(convert(return_data))}')
                    response = " ".join(convert(return_data))
                    responses.append(response)

                if not any("NSU" in response for response in responses):
                    success = True
        return success

    server_address = ("localhost", 16713)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

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
    curr_result = {}

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
            print(daide)

            if "MIS" in daide and self_power:
                """ ords, s, y = get_random_orders()
                if len(ords) > 0:
                    send_not_gof(sock)
                    send_order(sock, ords)
                    send_gof(sock) """
                pass


            if "HLO" in daide and any(power in daide for power in POWERS):
                print("assigned power:", daide[6:9])
                self_power = daide[6:9]

            if return_data == "4810" and daide == "OFF":
                # exit
                print("OFF message received, exiting...")
                break

            if "NOW" in daide:
                curr_result = {}
                info = process_now(daide.strip())
                phase, *units = info
                season, year_hex = phase.split(" ")
                year = hex_to_decimal(year_hex)
                print(f'Phase: {phase}, Year: {year}')
                now_phase = (int(year) - 1901) * 5


                if season == "SPR":
                    #assert game.phase.startswith("SPRING") and game.phase.endswith("MOVEMENT"), f"Expected {season} {year}, got {game.phase}"
                    now_phase += 1
                elif season == "SUM":
                    #assert game.phase.startswith("SPRING") and game.phase.endswith("RETREAT"), f"Expected {season} {year}, got {game.phase}"
                    now_phase += 2
                elif season == "FAL":
                    #assert game.phase.startswith("FALL") and game.phase.endswith("MOVEMENT"), f"Expected {season} {year}, got {game.phase}"
                    now_phase += 3
                elif season == "AUT":
                    #assert game.phase.startswith("SPRING") and game.phase.endswith("RETREAT"), f"Expected {season} {year}, got {game.phase}"
                    now_phase += 4
                elif season == "WIN":
                    #print(game.phase)
                    now_phase += 5

                engine_phase_abbr = game.get_current_phase()
                print(f"Engine phase: {engine_phase_abbr}")
                engine_season = engine_phase_abbr[0]
                engine_year = engine_phase_abbr[1:5]
                engine_phase = engine_phase_abbr[5]
                engine_phase_num = (int(engine_year) - 1901) * 5
                if engine_season == "S" and engine_phase == "M":
                    engine_phase_num += 1
                elif engine_season == "S" and engine_phase == "R":
                    engine_phase_num += 2
                elif engine_season == "F" and engine_phase == "M":
                    engine_phase_num += 3
                elif engine_season == "F" and engine_phase == "R":
                    engine_phase_num += 4
                elif engine_season == "W":
                    engine_phase_num += 5

                if engine_phase_num < now_phase:
                    for ii in range(now_phase - engine_phase_num):
                        game.process()
                        print(f"Processed phase {game.phase}")
                


                if self_power:
                    send_not_gof(sock)
                    gen_send_orders(sock)
                    send_gof(sock)


                """ for pp, orders in curr_result.items():
                    game.set_orders(POWER_NAMES[pp], orders) """


                #game.process()

            if "ORD" in daide:
                order_power = None
                print(f"ORD message received {daide}")
                phase, order, *rest = process_ord(daide.strip())

                if 'NSO' in rest:
                    print('NSO')
                    continue
                season, year_hex = phase.split(" ")
                year = hex_to_decimal(year_hex)

                for token in order.split(" "):
                    if token in POWER_NAMES:
                        order_power = token
                        break

                order = dipnet_order(order)

                if order_power not in curr_result:
                    curr_result[order_power] = []
                curr_result[order_power].append(order)
                print('curr_result:\n', curr_result)

                game.set_orders(POWER_NAMES[order_power], curr_result[order_power])



    except KeyboardInterrupt:
        print("Closing socket")
        sock.close()


if __name__ == "__main__":
    main()
