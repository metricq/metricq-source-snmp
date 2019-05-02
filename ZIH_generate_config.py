#!/usr/bin/python3

"""
Generate MetricQ SNMP source configuration or combinator configuration (in json format) for LZR PDUs
Requires a CMDB export file (pdu_lzr.csv) as input
"""

import csv
import json
from collections import OrderedDict
import click

PDU_CSV_FILE = "pdu_lzr.csv"

settings = {
    'default_community': 'pdumon',
    'default_interval': 5,
    'default_prefix': 'LZR.E98',
    'default_object_collections': ['default_objects'],
    'additional_metric_attributes': ['room', 'rack', 'unit'],
    'snmp_object_collections': {
        'default_objects': {
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.1': {  # power pro Phase
                'suffix': 'B83.W1',
                'unit': 'W',
                'short_description': 'Power Phase 1',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.2': {
                'suffix': 'B83.W2',
                'unit': 'W',
                'short_description': 'Power Phase 2',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.3': {
                'suffix': 'B83.W3',
                'unit': 'W',
                'short_description': 'Power Phase 3',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.1': {  # current pro Phase
                'multiplier': 0.01,
                'suffix': 'B81.L1',
                'unit': 'A',
                'short_description': 'Current Phase 1',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.2': {
                'multiplier': 0.01,
                'suffix': 'B81.L2',
                'unit': 'A',
                'short_description': 'Current Phase 2',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.3': {
                'multiplier': 0.01,
                'suffix': 'B81.L3',
                'unit': 'A',
                'short_description': 'Current Phase 3',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.1': {  # voltage pro Phase
                'multiplier': 0.1,
                'suffix': 'B82.L1',
                'unit': 'V',
                'short_description': 'Voltage Phase 1',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.2': {
                'multiplier': 0.1,
                'suffix': 'B82.L2',
                'unit': 'V',
                'short_description': 'Voltage Phase 2',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.3': {
                'multiplier': 0.1,
                'suffix': 'B82.L3',
                'unit': 'V',
                'short_description': 'Voltage Phase 3',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.1': {  # powerfactor pro Phase
                'multiplier': 0.1,
                'suffix': 'B84.L1',
                'unit': '',
                'short_description': 'Power Factor Phase 1',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.2': {
                'multiplier': 0.1,
                'suffix': 'B84.L2',
                'unit': '',
                'short_description': 'Power Factor Phase 2',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.3': {
                'multiplier': 0.1,
                'suffix': 'B84.L3',
                'unit': '',
                'short_description': 'Power Factor Phase 3',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.1': {  # power pro Stromkreis
                'suffix': 'B83.WA',
                'unit': 'W',
                'short_description': 'Power Circuit A',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.2': {
                'suffix': 'B83.WB',
                'unit': 'W',
                'short_description': 'Power Circuit B',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.3': {
                'suffix': 'B83.WC',
                'unit': 'W',
                'short_description': 'Power Circuit C',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.4': {
                'suffix': 'B83.WD',
                'unit': 'W',
                'short_description': 'Power Circuit D',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.5': {
                'suffix': 'B83.WE',
                'unit': 'W',
                'short_description': 'Power Circuit E',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.6': {
                'suffix': 'B83.WF',
                'unit': 'W',
                'short_description': 'Power Circuit F',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.1': {  # current pro Stromkreis
                'multiplier': 0.01,
                'suffix': 'B81.LA',
                'unit': 'A',
                'short_description': 'Current Circuit A',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.2': {
                'multiplier': 0.01,
                'suffix': 'B81.LB',
                'unit': 'A',
                'short_description': 'Current Circuit B',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.3': {
                'multiplier': 0.01,
                'suffix': 'B81.LC',
                'unit': 'A',
                'short_description': 'Current Circuit C',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.4': {
                'multiplier': 0.01,
                'suffix': 'B81.LD',
                'unit': 'A',
                'short_description': 'Current Circuit D',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.5': {
                'multiplier': 0.01,
                'suffix': 'B81.LE',
                'unit': 'A',
                'short_description': 'Current Circuit E',
            },
            '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.6': {
                'multiplier': 0.01,
                'suffix': 'B81.LF',
                'unit': 'A',
                'short_description': 'Current Circuit F',
            }
        },
        'temperature_sensor': {
            '.1.3.6.1.4.1.476.1.42.3.8.60.15.1.70.1.1.1': {
                'multiplier': 0.1,
                'suffix': 'B30',
                'unit': 'degC',
                'description': 'Temperature',
                'interval': 60,
            }
        }
    }
}


def read_pdu_csv():
    r = csv.reader(open(PDU_CSV_FILE, "r"), delimiter=";")
    ips = {}
    for ip, mac, room, c1, c2, c3, c4, rackpdu, cmdbname1, cmdbname2, cmdbname3, cmdbname4 in r:
        roomnum = int(room[1:])
        racks = [c1, c2, c3, c4]
        for rack in racks:
            if not rack:
                continue
            racknum = int(rack[:-1])
            side = rack[-1]
            rack = "S{:02}".format(racknum)

            infix = '{:02}{:02}{}'.format(roomnum, racknum, side)
            ips[ip] = {
                'name': cmdbname1,
                'room': room,
                'rack': rack,
                'infix': infix,
                'description': 'Room {} Rack {} PDU {}'.format(room, rack, side),
            }

    return ips


def out_combinator(ips):
    config = OrderedDict()
    racks = []
    for host_cfg in ips.values():
        rack = "{}.{}".format(
            settings['default_prefix'], host_cfg['infix'][:-1])
        if rack not in racks:
            racks.append(rack)

            for side in ["A", "B"]:
                expression = {
                    "operation": "+",
                    "left": {
                        "operation": "+",
                        "left": "{}{}.B83.W1".format(rack, side),
                        "right": "{}{}.B83.W2".format(rack, side)
                    },
                    "right": "{}{}.B83.W3".format(rack, side)
                }
                metadata = {
                    "description": "Room {} Rack {} PDU {} Power".format(host_cfg['room'], host_cfg['rack'], side),
                    "display_expression": "({}{}.B83.W1 + {}{}.B83.W2 + {}{}.B83.W3)".format(rack, side, rack, side, rack, side),
                    "unit": "W",
                }
                config["{}{}.B83.W".format(rack, side)] = {
                    "expression": expression, "metadata": metadata}

            expression = {
                "operation": "+",
                "left": "{}A.B83.W".format(rack),
                "right": "{}B.B83.W".format(rack)
            }
            metadata = {
                "description": "Room {} Rack {} Total Power".format(host_cfg['room'], host_cfg['rack']),
                "display_expression": "({}A.B83.W + {}B.B83.W)".format(rack, rack),
                "unit": "W",
            }
            config["{}.B83.W".format(rack)] = {
                "expression": expression, "metadata": metadata}
    return config


@click.command()
@click.option('--combinator', default=False, is_flag=True)
def main(combinator):
    ips = read_pdu_csv()
    if combinator:
        print(json.dumps(out_combinator(ips), indent=2))
    else:
        settings['hosts'] = ips
        print(json.dumps(settings, indent=2))


if __name__ == '__main__':
    main()
