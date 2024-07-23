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

def unit_to_daide(power, unit):
    assert len(unit) == 2
    unit_type = "FLT" if unit[0] == "F" else "AMY"

    return '( ' + power + ' ' + unit_type + ' ' + unit[1] + ' )'

def decimal_to_hex(decimal):
    return hex(decimal)[2:].zfill(4)

def dip_order_to_daide(power, order):
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
        daide += ' SUP ' + dip_order_to_daide(power, ' '.join(rest[1:]))
        return daide
    elif rest[0] == 'C':
        daide += ' CVY ' + unit_to_daide(power, rest[1:3])
        daide += ' CTO ' + rest[4]
        return daide

def cal_remaining_len(data):
    return len(data) // 2

server_address = ('localhost', 16713)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

# Connect to the server
sock.connect(server_address)
print(f'Connected to {server_address}')

message = '000000040001da10'

#nme_msg = '02000022480c40004b424b6f4b74400140004b764b364b2e4b304b2e4b314001'
nme_msg = '02000022480c40004b414b6c4b624b654b724b74400140004b764b364b2e4b304b2e4b314001'

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

    # MAXIMUM RECEIVED DATA SIZE = 65535
        data = sock.recv(65535)
        hex_data = data.hex()

    # wait for a HLO message
    # get power from HLO

    hlo_bytes = sock.recv(65535)
    hlo_hex = hlo_bytes.hex()
    hlo_msg = ' '.join(convert(hlo_hex))
    if any(power in hlo_msg for power in POWERS):
        print('assigned power:', hlo_msg[6:9])
        self_power = hlo_msg[6:9]

    sleep(1)
    not_gof = convert_to_hex(['NOT','(', 'GOF', ')'])
    len_not_gof = decimal_to_hex(cal_remaining_len(not_gof))


    sock.sendall(bytes.fromhex(DM_PREFIX + len_not_gof + not_gof))
    data = sock.recv(65535)

    hex_data = data.hex()

    with open('traffic.log', 'a') as f:
        f.write(' '.join(convert(hex_data)) + '\n')

    possible_orders = game.get_all_possible_orders()
    power_orders = [random.choice(possible_orders[loc]) for loc in game.get_orderable_locations(power_names[self_power]) if possible_orders[loc]]
    phase = game.phase
    year = phase.split(' ')[1]
    season = phase.split(' ')[0][:3]
    year_hex = decimal_to_hex(int(year))
    print(power_orders)
    daide_orders = [dip_order_to_daide(self_power, order) for order in power_orders]
    print(daide_orders)
    submit_orders = convert_to_hex(['SUB', '(', season, year_hex, ')'])
    for daide_order in daide_orders:
        pieces = daide_order.split(' ')
        submit_orders += convert_to_hex(['('])
        submit_orders += convert_to_hex(pieces)
        submit_orders += convert_to_hex([')'])

    sock.sendall(bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(submit_orders)) + submit_orders))

    data = sock.recv(65535)
    hex_data = data.hex()
    print(' '.join(convert(hex_data)))
    print(f'Received: {hex_data}')

    with open('traffic.log', 'a') as f:
        f.write(' '.join(convert(hex_data)) + '\n')

    gof = convert_to_hex(['GOF'])

    sock.sendall(bytes.fromhex(DM_PREFIX + decimal_to_hex(cal_remaining_len(gof)) + gof))


    data = sock.recv(65535)
    hex_data = data.hex()
    print(' '.join(convert(hex_data)))
    print(f'Received: {hex_data}')

    with open('traffic.log', 'a') as f:
        f.write(' '.join(convert(hex_data)) + '\n')



except KeyboardInterrupt:
    print('Closing socket')
    sock.close()
