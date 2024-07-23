import socket
import random

from convert import convert, convert_to_hex
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

def get_unit_power(game, unit):
    print('get_unit_power:', unit)
    loc_dict = game.get_orderable_locations()
    print('get_unit_power:', loc_dict)
    for pp, locs in loc_dict.items():
        if unit in locs:
            print('get_unit_power:', pp)
            return pp[:3]


def unit_to_daide(power, unit):
    assert len(unit) == 2
    unit_type = "FLT" if unit[0] == "F" else "AMY"

    return '( ' + power + ' ' + unit_type + ' ' + unit[1] + ' )'

def decimal_to_hex(decimal):
    return hex(decimal)[2:].zfill(4)

def dip_order_to_daide(power, order):
    print('dip_order_to_daide:', power, order)
    splitted = order.split(' ')       

    assert len(splitted) < 8 

    unit = splitted[:2]
    rest = splitted[2:]

    # U LOC -> ( POW UNT LOC )
    daide = unit_to_daide(power, unit)

    if len(rest) == 0 or (len(rest) == 1 and rest[0] == 'H'):
        daide += ' HLD'
        return daide
    elif len(rest) == 2 and rest[0] == '-':
        daide += ' MTO ' + rest[1]
        return daide
    elif rest[0] == 'S':
        supported_power = get_unit_power(game, rest[2])
        daide += ' SUP ' + dip_order_to_daide(supported_power, ' '.join(rest[1:]))
        return daide
    elif rest[0] == 'C':
        convoyed_power = get_unit_power(game, rest[2])
        daide += ' CVY ' + unit_to_daide(convoyed_power, rest[1:3])
        daide += ' CTO ' + rest[4]
        return daide

def hex_to_decimal(hex):
    return int(hex, 16)

def cal_remaining_len(data):
    return len(data) // 2

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
    daide_orders = [dip_order_to_daide(self_power, order) for order in power_orders]
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


try:
    for msg in to_send:
        # convert message to bytes
        msg = bytes.fromhex(msg)

        # Send data
        sock.sendall(msg)

        return_msg_type, return_data = read_data(sock)

        #print(return_msg_type)
        #print(' '.join(convert(return_data)))

    # MAXIMUM RECEIVED DATA SIZE = 65535
        #data = sock.recv(65535)
        #hex_data = data.hex()

    # wait for a HLO message
    # get power from HLO

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
