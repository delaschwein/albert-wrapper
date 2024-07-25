from wrapper import daidefy_order, dipnet_order
from diplomacy import Game

def test_daidefy_order():
    power = "ENG"
    game = Game()



    """hlds = {
        "A LVP H": "( ENG AMY LVP ) HLD",
        "F EDI H": "( ENG FLT EDI ) HLD",
    }

    for order, expected in hlds.items():
        result = daidefy_order(power, order)
        assert result == expected

    mtos = {
        "A LVP - YOR": "( ENG AMY LVP ) MTO YOR",
        "F EDI - NTH": "( ENG FLT EDI ) MTO NTH",
    }

    for order, expected in mtos.items():
        result = daidefy_order(power, order)
        assert result == expected

    sup_hld = {
        "F EDI S A LVP H": "( ENG FLT EDI ) SUP ( ENG AMY LVP )",
        "A LVP S F EDI H": "( ENG AMY LVP ) SUP ( ENG FLT EDI )",
    }

    for order, expected in sup_hld.items():
        result = daidefy_order(power, order)
        assert result == expected


    sup_mto = {
        "F EDI S A LVP - YOR": "( ENG FLT EDI ) SUP ( ENG AMY LVP ) MTO YOR",
        "F LON S A LVP - WAL": "( ENG FLT LON ) SUP ( ENG AMY LVP ) MTO WAL",
    }

    for order, expected in sup_mto.items():
        result = daidefy_order(power, order)
        print(result, expected)
        assert result == expected


    cvys = {
        "F NTH C A YOR - HOL": "( ENG FLT NTH ) CVY ( ENG AMY YOR ) CTO HOL",
        "F NTH C A YOR - BEL": "( ENG FLT NTH ) CVY ( ENG AMY YOR ) CTO BEL",
    }
    game.set_orders("ENGLAND", ['A LVP - YOR', 'F EDI - NTH', 'F LON - ENG'])

    game.process()

    for order, expected in cvys.items():
        result = daidefy_order(game, power, order)
        print(result, expected)
        assert result == expected


    game.set_orders("ENGLAND", ['A LVP - YOR', 'F EDI - NTH', 'F LON - ENG'])

    game.process()

    ctos = {
        "A YOR - HOL VIA": "( ENG AMY YOR ) CTO HOL VIA ( NTH )",
        "A YOR - BEL VIA": "( ENG AMY YOR ) CTO BEL VIA ( NTH )",
    }

    for order, expected in ctos.items():
        result = daidefy_order(game, power, order, ["NTH"])
        assert result == expected

    game.set_orders("ENGLAND", ['A LVP - YOR', 'F EDI - NTH', 'F LON - ENG'])
    game.process()
    game.set_orders("ENGLAND", ['F NTH C YOR - HOL', 'A YOR - HOL VIA', 'F ENG H'])
    game.process()

    bld = {
        "A LVP B": "( ENG AMY LVP ) BLD",
    }

    for order, expected in bld.items():
        result = daidefy_order(game, power, order)
        print(result, expected)
        assert result == expected


    game.set_orders("ENGLAND", ['A LVP - YOR', 'F EDI - NTH', 'F LON - ENG'])
    game.process()
    game.set_orders("ENGLAND", ['F NTH C YOR - HOL', 'A YOR - HOL VIA', 'F ENG H'])
    game.process()
    game.set_orders("ENGLAND", ['A LVP B'])
    game.process()
    game.set_orders("GERMANY", ['A MUN - RUH'])
    game.process()
    game.set_orders("GERMANY", ['F KIE S A RUH - HOL', 'A RUH - HOL'])
    game.process()

    rto = {
        "A HOL R BEL": "( ENG AMY HOL ) RTO BEL",
    }

    dsb = {
        "A HOL D": "( ENG AMY HOL ) DSB",
    }

    for order, expected in rto.items():
        result = daidefy_order(game, power, order)
        print(result, expected)
        assert result == expected

    for order, expected in dsb.items():
        result = daidefy_order(game, power, order, [], True)
        print(result, expected)
        assert result == expected

    game.set_orders("ENGLAND", ['A LVP - YOR', 'F EDI - NTH', 'F LON - ENG'])
    game.process()
    game.set_orders("ENGLAND", ['F NTH C YOR - HOL', 'A YOR - HOL VIA', 'F ENG H'])
    game.process()
    game.set_orders("ENGLAND", ['A LVP B'])
    game.process()
    game.set_orders("GERMANY", ['A MUN - RUH'])
    game.process()
    game.set_orders("GERMANY", ['F KIE S A RUH - HOL', 'A RUH - HOL'])
    game.process()
    game.set_orders("ENGLAND", ['A HOL R BEL'])
    game.process()
    game.set_orders("GERMANY", ['A MUN B'])
    game.process()
    game.set_orders("GERMANY", ['A MUN - RUH'])
    game.process()
    game.set_orders("GERMANY", ['A RUH S A HOL - BEL', 'A HOL - BEL'])
    game.process()
    game.set_orders("ENGLAND", ['A BEL R PIC'])
    game.process()

    rem = {
        "A PIC D": "( ENG AMY PIC ) REM",
    }

    for order, expected in rem.items():
        result = daidefy_order(game, power, order)
        print(result, expected)
        assert result == expected
"""

def test_dipnet_order():
    hlds = {
        "A LVP H": "( ENG AMY LVP ) HLD",
        "F STP/SC H": "( RUS FLT ( STP SCS ) ) HLD",
    }

    mtos = {
        "A LVP - YOR": "( ENG AMY LVP ) MTO YOR",
        "F STP/SC - FIN": "( RUS FLT ( STP SCS ) ) MTO FIN",
    }
    sup_hld = {
        "F STP/SC S A MOS H": "( RUS FLT ( STP SCS ) ) SUP ( RUS AMY MOS )",
        "A LVP S F EDI H": "( ENG AMY LVP ) SUP ( ENG FLT EDI )",
    }

    sup_mto = {
        "F STP/SC S A MOS - LVN": "( RUS FLT ( STP SCS ) ) SUP ( RUS AMY MOS ) MTO LVN",
        "F LON S A LVP - WAL": "( ENG FLT LON ) SUP ( ENG AMY LVP ) MTO WAL",
    }

    cvys = {
        "F NTH C A YOR - HOL": "( ENG FLT NTH ) CVY ( ENG AMY YOR ) CTO HOL",
        "F NTH C A YOR - BEL": "( ENG FLT NTH ) CVY ( ENG AMY YOR ) CTO BEL",
    }

    ctos = {
        "A YOR - HOL VIA": "( ENG AMY YOR ) CTO HOL VIA ( NTH )",
        "A YOR - BEL VIA": "( ENG AMY YOR ) CTO BEL VIA ( NTH )",
    }

    bld = {
        "A LVP B": "( ENG AMY LVP ) BLD",
    }

    rto = {
        "A HOL R BEL": "( ENG AMY HOL ) RTO BEL",
    }

    dsb = {
        "A HOL D": "( ENG AMY HOL ) DSB",
    }

    rem = {
        "A PIC D": "( ENG AMY PIC ) REM",
    }

    to_test = [hlds, mtos, sup_hld, sup_mto, cvys, ctos, bld, rto, dsb, rem]

    for test in to_test:
        for dipnet, daide in test.items():
            result = dipnet_order(daide)
            assert result == dipnet, f"{result} != {dipnet}"

if __name__ == "__main__":
    test_daidefy_order()
    #test_dipnet_order()
