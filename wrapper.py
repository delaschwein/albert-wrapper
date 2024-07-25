import socket
import random
from typing_extensions import List

#from convert import convert, convert_to_hex
from time import sleep
from diplomacy import Game

power_names = {
    "AUS": "AUSTRIA",
    "ENG": "ENGLAND",
    "FRA": "FRANCE",
    "GER": "GERMANY",
    "ITA": "ITALY",
    "RUS": "RUSSIA",
    "TUR": "TURKEY"
}

game = Game()

dipnet2daide_loc = {
    "BOT": "GOB",
    "ENG": "ECH",
    "LYO": "GOL",
}

daide2dipnet_loc = {v: k for k, v in dipnet2daide_loc.items()}


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

def dipnet_location(loc: str) -> str:
    if ' ' in loc:
        loc = loc.replace('(', '').replace(')', '')
        prov, coast = loc.split(' ')
        prov = prov.strip()
        coast = coast.strip()
        return '/'.join([prov, coast[:-1]])
    else:
        if loc in daide2dipnet_loc:
            return daide2dipnet_loc[loc]

    return loc

def daidefy_location(loc: str) -> str:
    """Converts DipNet-style location to DAIDE-style location

    E.g.
    BUL/EC --> ( BUL ECS )
    STP/SC --> ( STP SCS )
    ENG    --> ECH
    PAR    --> PAR

    :param loc: DipNet-style province notation
    :return: DAIDE-style loc
    """
    if '/' in loc:
        prov, coast = loc.split('/')
        coast += "S"
        return ' '.join(['(', prov, coast, ')'])
    else:
        if loc in dipnet2daide_loc:
            return dipnet2daide_loc[loc]

    return loc

def dipnet_unit(unit: List[str]):
    assert len(unit) == 5 or len(unit) == 8
    if len(unit) == 5:
        # non coastal
        unit = unit[2:4]
        unit_type = unit[0][0]
        loc = dipnet_location(unit[1])
        return unit_type + ' ' + loc
    else:
        # coastal
        unit = unit[2:7]
        unit_type = unit[0][0]
        loc = dipnet_location(' '.join(unit[2:4]))
        return unit_type + ' ' + loc

def daidefy_unit(unit: List[str]):
    """Converts DipNet-style unit to DAIDE-style unit

    E.g. (for initial game state)
    A BUD --> AUS AMY BUD
    F TRI --> AUS FLT TRI
    A PAR --> FRA AMY PAR
    A MAR --> FRA AMY MAR

    :param dipnet_unit: DipNet-style unit notation
    :param unit_game_mapping: Mapping from DipNet-style units to powers
    :return: DAIDE-style unit
    """

    assert len(unit) == 2
    unit_type = "FLT" if unit[0] == "F" else "AMY"
    loc = daidefy_location(unit[1])
    if len(loc) > 3:
        loc = loc[:3]
    pow = get_unit_power(game, loc)
    return ' '.join(['(', pow, unit_type, loc, ')'])

def get_unit_power(game: Game, unit: str) -> str:
    #print('get_unit_power:', unit)
    loc_dict = game.get_orderable_locations()
    #print('get_unit_power:', loc_dict)
    for pp, locs in loc_dict.items():
        if unit in locs:
            #print('get_unit_power:', pp)
            return pp[:3]

def decimal_to_hex(decimal):
    return hex(decimal)[2:].zfill(4)

def dipnet_order(order: str) -> str:
    splitted = order.split(' ')
    is_coastal = splitted[3] == '('

    if is_coastal:
        unit = splitted[0:8]
        rest = splitted[8:]
    else:
        unit = splitted[0:5]
        rest = splitted[5:]

    dipnet_u = dipnet_unit(unit)

    if len(rest) == 1:
        # HLD/BLD/DSB/REM
        if rest[0] == 'REM':
            return dipnet_u + ' D'
        else:
            return dipnet_u + ' ' + rest[0][0]
    elif len(rest) == 2:
        # MTO/RTO
        if rest[0] == 'RTO':
            return dipnet_u + ' R ' + dipnet_location(rest[1])
        else:
            return dipnet_u + ' - ' + dipnet_location(rest[1])
    else:
        move_type = rest[0]
        if move_type == 'CTO':
            return dipnet_u + ' - ' + dipnet_location(rest[1]) + ' VIA'
        elif move_type == 'CVY':
            cvy_unit = dipnet_unit(rest[1:6])
            cto_loc = dipnet_location(rest[7])
            return dipnet_u + ' C ' + cvy_unit + ' - ' + cto_loc
        else:
            len_sup = len(rest)
            if len_sup == 6:
                sup_unit = dipnet_unit(rest[1:])
                return dipnet_u + ' S ' + sup_unit + ' H'
            elif len_sup == 8:
                sub_order = dipnet_order(' '.join(rest[1:]))
                return dipnet_u + ' S ' + sub_order
            else:
                raise ValueError(f"Invalid sup order: {order}")

    raise ValueError(f"Invalid order: {order}")


def daidefy_order(game: Game, power: str, order: str, via_locs: list = [], dsb: bool = False) -> str:
    splitted = order.split(' ')
    unit_type, loc, *rest = splitted
    #loc = loc if '/' not in loc else loc.split('/')[0]
    daide_unit_type = 'FLT' if unit_type == 'F' else 'AMY'
    daide_loc = daidefy_location(loc)
    if ' ' in daide_loc:
        primary_unit_power = get_unit_power(game, daide_loc.split(' ')[1])
    else:
        primary_unit_power = get_unit_power(game, daide_loc)
    assert primary_unit_power == power, f"Power mismatch: {power} != {primary_unit_power}"

    daide_primary_unit = ' '.join(['(', primary_unit_power, daide_unit_type, daide_loc, ')'])

    if rest[0] == '-':
        # either MTO or CTO
        if 'VIA' in rest:
            # CTO
            assert len(rest) == 3, f"CTO order has more than 3 elements: {order}"
            to_loc = rest[1]

            daide_to_loc = daidefy_location(to_loc)

            return daide_primary_unit + ' CTO ' + daide_to_loc + ' VIA ' + '( ' + ' '.join(via_locs) + ' )'

        else:
            # MTO
            assert len(rest) == 2, f"MTO order has more than 2 elements: {order}"
            to_loc = rest[1]
            daide_to_loc = daidefy_location(to_loc)

            return daide_primary_unit + ' MTO ' + daide_to_loc
    else:
        if 'R' in rest:
            # RTO
            assert len(rest) == 2, f"RTO order has more than 2 elements: {order}"
            to_loc = rest[1]
            daide_to_loc = daidefy_location(to_loc)

            return daide_primary_unit + ' RTO ' + daide_to_loc
        elif 'B' in rest:
            # BLD
            assert len(rest) == 1, f"BLD order has more than 1 element: {order}"
            return daide_primary_unit + ' BLD'
        elif 'D' in rest:
            # DSB or REM
            assert len(rest) == 1, f"DSB/REM order has more than 1 element: {order}"
            if dsb:
                return daide_primary_unit + ' DSB'
            else:
                return daide_primary_unit + ' REM'
        elif 'S' in rest or 'C' in rest:
            # SUP/CVY
            assert len(rest) > 3, f"SUP/CVY order has less than 4 elements: {order}"
            secondary_loc = rest[2]

            if '/' in secondary_loc:
                secondary_power = get_unit_power(game, secondary_loc.split('/')[0])
            else:
                secondary_power = get_unit_power(game, secondary_loc)

            secondary_move = daidefy_order(game, secondary_power, ' '.join(rest[1:]))
            if 'S' in rest:
                result = daide_primary_unit + ' SUP ' + secondary_move

                if 'H' in rest:
                    return result.replace(' HLD', '')

                return result
            else:
                assert 'C' in rest, f"CVY order has no 'C' element: {order}"

                result = daide_primary_unit + ' CVY ' + secondary_move
                return result.replace('MTO', 'CTO')

        elif 'H' in rest:
            # HLD
            assert len(rest) == 1, f"HLD order has more than 1 element: {order}"
            return daide_primary_unit + ' HLD'

def hex_to_decimal(hex):
    return int(hex, 16)

def cal_remaining_len(data):
    return len(data) // 2

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
        not_gof = convert_to_hex(['NOT','(', 'GOF', ')'])
        len_not_gof = decimal_to_hex(cal_remaining_len(not_gof))

        sock.sendall(bytes.fromhex(DM_PREFIX + len_not_gof + not_gof))

        message_type, rest = read_data(sock)
        print(message_type, ' '.join(convert(rest)))

        # generate, convert from shorthand to daide, send
        possible_orders = game.get_all_possible_orders()
        power_orders = [random.choice(possible_orders[loc]) for loc in game.get_orderable_locations(power_names[self_power]) if possible_orders[loc]]
        phase = game.phase
        year = phase.split(' ')[1]
        season = phase.split(' ')[0][:3]
        year_hex = decimal_to_hex(int(year))

        print("Converting:", power_orders)
        daide_orders = [daidefy_order(game, self_power, order) for order in power_orders]
        print("Converted:", daide_orders)

        submit_orders = convert_to_hex(['SUB', '(', season, year_hex, ')'])

        for daide_order in daide_orders:
            pieces = daide_order.split(' ')
            submit_orders += convert_to_hex(['('])
            submit_orders += convert_to_hex(pieces)
            submit_orders += convert_to_hex([')'])

        sock.sendall(bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(submit_orders)) + submit_orders))

        message_type, rest = read_data(sock)
        print(message_type, ' '.join(convert(rest)))

        gof = convert_to_hex(['GOF'])

        sock.sendall(bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(gof)) + gof))

        message_type, rest = read_data(sock)
        print(message_type, ' '.join(convert(rest)))


    server_address = ('localhost', 16713)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Connect to the server
    sock.connect(server_address)
    print(f'Connected to {server_address}')

    message = '000000040001da10'

    nme_msg = '0200001c480c40004b424b6f4b74400140004b764b364b2e4b304b2e4b314001'
    #nme_msg = '02000022480c40004b414b6c4b624b654b724b74400140004b764b364b2e4b304b2e4b314001'

    mdf_msg = '02f40002480a'

    yes_map_standard = '0200001c481c4000480940004b534b544b414b4e4b444b414b524b4440014001'

    to_send = [message, nme_msg, mdf_msg, yes_map_standard]

    POWERS = ['AUS', 'ENG', 'FRA', 'GER', 'ITA', 'RUS', 'TUR']

    DM_PREFIX = '0200'

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

            daide = ' '.join(convert(return_data))

            if any(power in daide for power in POWERS):
                print('assigned power:', daide[6:9])
                self_power = daide[6:9]

            if return_data == '4810' and daide == 'OFF':
                # exit
                print('OFF message received, exiting...')
                break

            if self_power:
                send_order(sock, [])
                break


    except KeyboardInterrupt:
        print('Closing socket')
        sock.close()


if __name__ == '__main__':
    main()
