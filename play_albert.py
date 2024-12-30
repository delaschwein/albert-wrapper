from concurrent.futures._base import Future
import socket
import random
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
from time import sleep
from scapy.all import sniff, TCP, IP


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
    process_mrt,
    process_frm,
)

from diplomacy import Game
from diplomacy import Message
from diplomacy.client.network_game import NetworkGame

ASSIGNED_ALBERT_POWER = 'AUS' # Albert's power in Paquette game
POWERS = ["AUS", "ENG", "FRA", "GER", "ITA", "RUS", "TUR"]
DM_PREFIX = "0200"
NETWORK_INTERFACE = "\\Device\\NPF_Loopback"


game = Game()
#game.add_rule("DONT_SKIP_PHASES")


def imitator(input_queues: dict[str, list[str]], result_queue):
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

            print("Sending orders:", orders, submit_orders)

            sock.sendall(
                bytes.fromhex(
                    DM_PREFIX
                    + decimal_to_hex(cal_remaining_len(submit_orders))
                    + submit_orders
                )
            )

    def gen_send_orders(sock):
        """
        Generate random orders and send them to the server until success
        """
        # ords, s, y = get_random_orders()

        ords = input_queues[self_power]

        send_order(sock, ords)

        for ii in range(len(ords)):
            return_msg_type, return_data = read_data(sock)
            response = " ".join(convert(return_data))
            if "NSU" in response:
                print("Orders not sent successfully", response)

    server_address = ("localhost", 16713)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)

    message = "000000040001da10"
    nme_msg = "0200001c480c40004b424b6f4b74400140004b764b364b2e4b304b2e4b314001"
    mdf_msg = "02f40002480a"
    yes_map_standard = (
        "0200001c481c4000480940004b534b544b414b4e4b444b414b524b4440014001"
    )

    to_send = [message, nme_msg, mdf_msg, yes_map_standard]


    self_power = None
    curr_result = {}

    try:
        for msg in to_send:
            msg = bytes.fromhex(msg)
            # Send data
            sock.sendall(msg)
            return_msg_type, return_data = read_data(sock)

        while True:
            return_msg_type, return_data = read_data(sock)

            daide = " ".join(convert(return_data))

            if "MIS" in daide and self_power:
                retreat_power, dipnet_u, dipnet_retreat_locs = process_mrt(
                    daide.strip()
                )
                game_power = game.get_power(POWER_NAMES[retreat_power])
                game_power.retreats[dipnet_u] = dipnet_retreat_locs
                send_not_gof(sock)
                gen_send_orders(sock)
                send_gof(sock)

            if "HLO" in daide and any(power in daide for power in POWERS):
                self_power = daide[6:9]
                result_queue.put(("HLO", self_power))

            if return_data == "4810" and daide == "OFF":
                break

            if "SCO" in daide:
                dist = process_sco(daide.strip())
                game.clear_centers()
                for power, centers in dist.items():
                    game.set_centers(power, centers)

            if "NOW" in daide:
                info = process_now(daide.strip())
                phase, *units = info
                season, year_hex = phase.split(" ")
                year = str(hex_to_decimal(year_hex))

                if "MRT" in daide:
                    game.process()
                    send_not_gof(sock)
                    gen_send_orders(sock)
                    send_gof(sock)
                    continue

                curr_result = {}
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

                # send orders if power assigned
                if self_power:
                    send_not_gof(sock)
                    gen_send_orders(sock)
                    send_gof(sock)
                    # send some random messages
                    """ for recipient in POWERS:
                        if recipient != self_power:
                            for against in POWERS:
                                if against != self_power and against != recipient:
                                    to_send = ["PRP", "(", "ALY", "(", self_power, recipient, ")", "VSS", "(", against, ")", ")"]
                                    send_msg(sock, to_send, [recipient], season, year_hex)
                                    pce = ["PRP", "(", "PCE", "(", self_power, recipient, ")", ")"]
                                    send_msg(sock, pce, [recipient], season, year_hex)
                                    print("sending", ' '.join(to_send)) """

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

            if "FRM" in daide:
                sender, recipients, msg = process_frm(daide.strip())
                for rr in recipients:
                    game.add_message(
                        Message(
                            sender=POWER_NAMES[sender],
                            recipient=POWER_NAMES[rr],
                            message=msg,
                            phase=game.get_current_phase(),
                            time_sent=int(time.time()),
                        )
                    )

    except KeyboardInterrupt:
        sock.close()

def six_imitators():
    """
        Run 6 imitators to parse Paquette game content to play with Albert
    """
    result_queue = queue.Queue()
    threads = 6
    input_queues = {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        for thread_id in range(threads):
            executor.submit(imitator, input_queues, result_queue)

        initialized_powers = set()
        while len(initialized_powers) < threads:
            try:
                flag, result = result_queue.get(timeout=1)
                if flag == "HLO":
                    initialized_powers.add(result)
                    input_queues[result] = queue.Queue()
            except queue.Empty:
                print("Waiting for all imitators to be assigned power")


        existing_powers = list(input_queues.keys())
        albert_power = [x for x in POWERS if x not in existing_powers][0]
        print(f"Albert is assigned {albert_power}")

        if albert_power != ASSIGNED_ALBERT_POWER:
            return False
        else:
            # getting albert's moves
            def packet_callback(packet):
                if IP in packet and TCP in packet:
                    if packet[TCP].sport == 16713:
                        payload = bytes(packet[TCP].payload)
                        if payload:
                            content = convert(payload.hex())
                            if "THX" in content:
                                content = content[4:-4]
                                power = content[1]

                                if power == ASSIGNED_ALBERT_POWER:                                
                                    print(" ".join(content))

            sniff(iface=NETWORK_INTERFACE, filter="tcp and src port 16713", prn=packet_callback, store=False)


            current_phase = 'S1901M'
            while True:
                # wait for moves on Paquette game
                for power in existing_powers:
                    command = "not_gof"
                    input_queues[power].put(command)

                # get Albert's moves


                



            return True


if __name__ == "__main__":
    while not six_imitators():
        continue
