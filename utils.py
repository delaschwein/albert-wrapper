from dip import Game
from typing import List

# convert 4B to ascii

HEX2DAIDE = {
    "4000": "(",
    "4001": ")",
    "4100": "AUS",
    "4101": "ENG",
    "4102": "FRA",
    "4103": "GER",
    "4104": "ITA",
    "4105": "RUS",
    "4106": "TUR",
    "4200": "AMY",
    "4201": "FLT",
    "4320": "CTO",
    "4321": "CVY",
    "4322": "HLD",
    "4323": "MTO",
    "4324": "SUP",
    "4325": "VIA",
    "4340": "DSB",
    "4341": "RTO",
    "4380": "BLD",
    "4381": "REM",
    "4382": "WVE",
    "4400": "MBV",
    "4401": "BPR",
    "4402": "CST",
    "4403": "ESC",
    "4404": "FAR",
    "4405": "HSC",
    "4406": "NAS",
    "4407": "NMB",
    "4408": "NMR",
    "4409": "NRN",
    "440A": "NRS",
    "440B": "NSA",
    "440C": "NSC",
    "440D": "NSF",
    "440E": "NSP",
    "440F": "NST",
    "4410": "NSU",
    "4411": "NVR",
    "4412": "NYU",
    "4413": "YSC",
    "4500": "SUC",
    "4501": "BNC",
    "4502": "CUT",
    "4503": "DSR",
    "4504": "FLD",
    "4505": "NSO",
    "4506": "RET",
    "4600": "NCS",
    "4602": "NEC",
    "4604": "ECS",
    "4606": "SEC",
    "4608": "SCS",
    "460A": "SWC",
    "460C": "WCS",
    "460E": "NWC",
    "4700": "SPR",
    "4701": "SUM",
    "4702": "FAL",
    "4703": "AUT",
    "4704": "WIN",
    "4800": "CCD",
    "4801": "DRW",
    "4802": "FRM",
    "4803": "GOF",
    "4804": "HLO",
    "4805": "HST",
    "4806": "HUH",
    "4807": "IAM",
    "4808": "LOD",
    "4809": "MAP",
    "480A": "MDF",
    "480B": "MIS",
    "480C": "NME",
    "480D": "NOT",
    "480E": "NOW",
    "480F": "OBS",
    "4810": "OFF",
    "4811": "ORD",
    "4812": "OUT",
    "4813": "PRN",
    "4814": "REJ",
    "4815": "SCO",
    "4816": "SLO",
    "4817": "SND",
    "4818": "SUB",
    "4819": "SVE",
    "481A": "THX",
    "481B": "TME",
    "481C": "YES",
    "481D": "ADM",
    "4900": "AOA",
    "4901": "BTL",
    "4902": "ERR",
    "4903": "LVL",
    "4904": "MRT",
    "4905": "MTL",
    "4906": "NPB",
    "4907": "NPR",
    "4908": "PDA",
    "4909": "PTL",
    "490A": "RTL",
    "490B": "UNO",
    "490D": "DSD",
    "4A00": "ALY",
    "4A01": "AND",
    "4A02": "BWX",
    "4A03": "DMZ",
    "4A04": "ELS",
    "4A05": "EXP",
    "4A06": "FWD",
    "4A07": "FCT",
    "4A08": "FOR",
    "4A09": "HOW",
    "4A0A": "IDK",
    "4A0B": "IFF",
    "4A0C": "INS",
    "4A0D": "IOU",
    "4A0E": "OCC",
    "4A0F": "ORR",
    "4A10": "PCE",
    "4A11": "POB",
    "4A12": "PPT",
    "4A13": "PRP",
    "4A14": "QRY",
    "4A15": "SCD",
    "4A16": "SRY",
    "4A17": "SUG",
    "4A18": "THK",
    "4A19": "THN",
    "4A1A": "TRY",
    "4A1B": "UOM",
    "4A1C": "VSS",
    "4A1D": "WHT",
    "4A1E": "WHY",
    "4A1F": "XDO",
    "4A20": "XOY",
    "4A21": "YDO",
    "4A22": "WRT",
    "5000": "BOH",
    "5001": "BUR",
    "5002": "GAL",
    "5003": "RUH",
    "5004": "SIL",
    "5005": "TYR",
    "5006": "UKR",
    "5107": "BUD",
    "5108": "MOS",
    "5109": "MUN",
    "510A": "PAR",
    "510B": "SER",
    "510C": "VIE",
    "510D": "WAR",
    "520E": "ADR",
    "520F": "AEG",
    "5210": "BAL",
    "5211": "BAR",
    "5212": "BLA",
    "5213": "EAS",
    "5214": "ECH",
    "5215": "GOB",
    "5216": "GOL",
    "5217": "HEL",
    "5218": "ION",
    "5219": "IRI",
    "521A": "MAO",
    "521B": "NAO",
    "521C": "NTH",
    "521D": "NWG",
    "521E": "SKA",
    "521F": "TYS",
    "5220": "WES",
    "5421": "ALB",
    "5422": "APU",
    "5423": "ARM",
    "5424": "CLY",
    "5425": "FIN",
    "5426": "GAS",
    "5427": "LVN",
    "5428": "NAF",
    "5429": "PIC",
    "542A": "PIE",
    "542B": "PRU",
    "542C": "SYR",
    "542D": "TUS",
    "542E": "WAL",
    "542F": "YOR",
    "5530": "ANK",
    "5531": "BEL",
    "5532": "BER",
    "5533": "BRE",
    "5534": "CON",
    "5535": "DEN",
    "5536": "EDI",
    "5537": "GRE",
    "5538": "HOL",
    "5539": "KIE",
    "553A": "LON",
    "553B": "LVP",
    "553C": "MAR",
    "553D": "NAP",
    "553E": "NWY",
    "553F": "POR",
    "5540": "ROM",
    "5541": "RUM",
    "5542": "SEV",
    "5543": "SMY",
    "5544": "SWE",
    "5545": "TRI",
    "5546": "TUN",
    "5547": "VEN",
    "5748": "BUL",
    "5749": "SPA",
    "574A": "STP",
}

DAIDE2HEX = {v: k for k, v in HEX2DAIDE.items()}

POWER_NAMES = {
    "AUS": "AUSTRIA",
    "ENG": "ENGLAND",
    "FRA": "FRANCE",
    "GER": "GERMANY",
    "ITA": "ITALY",
    "RUS": "RUSSIA",
    "TUR": "TURKEY"
}

DIPNET2DAIDE_LOC = {
    "BOT": "GOB",
    "ENG": "ECH",
    "LYO": "GOL",
}

DAIDE2DIPNET_LOC = {v: k for k, v in DIPNET2DAIDE_LOC.items()}


def split_by_two_characters(s):
    return [s[i:i+2] for i in range(0, len(s), 2)]

def convert(payload):
    octets = split_by_two_characters(payload)

    new_octets = []

    # fix the octets
    for oo in octets:
        if len(oo) == 6:
            new_octets.append(oo[:2])
            new_octets.append(oo[2:4])
            new_octets.append(oo[4:])
        else:
            new_octets.append(oo)

    out = []
    curr = []

    while len(new_octets) > 0:
        item = new_octets.pop(0)
        curr.append(item)

        if len(curr) == 2:
            out.append(''.join(curr))
            curr = []

    result = []

    for x in out:
        if x[:2].upper() == "4B":
            decimal = int(x[2:], 16)
            result.append(chr(decimal))
        
        else:
            if x.upper() in HEX2DAIDE:
                result.append(HEX2DAIDE[x.upper()])
            else:
                result.append(x)

    return result


def convert_to_hex(message):
    return ''.join([DAIDE2HEX.get(c, c) for c in message]).lower()


def dipnet_location(loc: str) -> str:
    if ' ' in loc:
        loc = loc.replace('(', '').replace(')', '')
        prov, coast = loc.split(' ')
        prov = prov.strip()
        coast = coast.strip()
        return '/'.join([prov, coast[:-1]])
    else:
        if loc in DAIDE2DIPNET_LOC:
            return DAIDE2DIPNET_LOC[loc]

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
        if loc in DIPNET2DAIDE_LOC:
            return DIPNET2DAIDE_LOC[loc]

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

def daidefy_unit(game: Game, unit: List[str]):
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