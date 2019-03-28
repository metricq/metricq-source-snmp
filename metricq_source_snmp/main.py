#!/usr/bin/python

import asyncio
from pprint import pprint
import time
import csv
import sys
from collections import OrderedDict, defaultdict
import multiprocessing as mp
from queue import Empty
import logging
import signal
import functools
import click
import click_log
import aiomonitor
import metricq
from config import server, token
from pysnmp.hlapi.asyncio import *
from metricq.logging import get_logger

INTERVAL = 5

logger = get_logger()
click_log.basic_config(logger)
logger.setLevel('ERROR')
# Use this if we ever use threads
# logger.handlers[0].formatter = logging.Formatter(fmt='%(asctime)s %(threadName)-16s %(levelname)-8s %(message)s')
logger.handlers[0].formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s')
orig_sig_handler = None

settings = {
  'prefix' : 'LZR.E98',
  'snmp_objects': {
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.1': { # power pro Phase
       'suffix': 'B83.W1',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.2': {
       'suffix': 'B83.W2',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.3': {
       'suffix': 'B83.W3',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.1': {  # current pro Phase
       'suffix': 'B81.L1',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.2': {
       'suffix': 'B81.L2',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.3': {
       'suffix': 'B81.L3',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.1': {  # voltage pro Phase
       'suffix': 'B82.L1',
       'unit': 'V',
       'short_description': 'Voltage',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.2': {
       'suffix': 'B82.L2',
       'unit': 'V',
       'short_description': 'Voltage',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.3': {
       'suffix': 'B82.L3',
       'unit': 'V',
       'short_description': 'Voltage',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.1': {  # powerfactor pro Phase
       'suffix': 'B84.L1',
       'unit': '',
       'short_description': 'Power Factor',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.2': {
       'suffix': 'B84.L2',
       'unit': '',
       'short_description': 'Power Factor',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.3': {
       'suffix': 'B84.L3',
       'unit': '',
       'short_description': 'Power Factor',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.1': { # power pro Stromkreis
       'suffix': 'B83.WA',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.2': {
       'suffix': 'B83.WB',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.3': {
       'suffix': 'B83.WC',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.4': {
       'suffix': 'B83.WD',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.5': {
       'suffix': 'B83.WE',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.6': {
       'suffix': 'B83.WF',
       'unit': 'W',
       'short_description': 'Power',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.1': {  # current pro Stromkreis
       'suffix': 'B81.LA',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.2': {
       'suffix': 'B81.LB',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.3': {
       'suffix': 'B81.LC',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.4': {
       'suffix': 'B81.LD',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.5': {
       'suffix': 'B81.LE',
       'unit': 'A',
       'short_description': 'Current',
    },
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.6': {
       'suffix': 'B81.LF',
       'unit': 'A',
       'short_description': 'Current',
    }
}

# order is relevant to assign results to the corresponding counters
counter_types = [
    "B83.W1",
    "B83.W2",
    "B83.W3",
    "B81.L1",
    "B81.L2",
    "B81.L3",
    "B82.L1",
    "B82.L2",
    "B82.L3",
    'B84.L1',
    'B84.L2',
    'B84.L3',
    'B83.WA',
    'B83.WB',
    'B83.WC',
    'B83.WD',
    'B83.WE',
    'B83.WF',
    'B81.LA',
    'B81.LB',
    'B81.LC',
    'B81.LD',
    'B81.LE',
    'B81.LF',
]
multis = [1.0, 1.0, 1.0, 0.01, 0.01, 0.01, 0.1, 0.1, 0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]

# again, order is relevant!
oids = [
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.1',  # power pro Phase
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.1',  # current pro Phase
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.1',  # voltage pro Phase
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.1',  # powerfactor pro Phase
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.1',  # power pro Stromkreis
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.4',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.5',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.6',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.1',  # current pro Stromkreis
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.2',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.3',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.4',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.5',
    '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.6',
]
objs = [ObjectType(ObjectIdentity(obj)) for obj in oids]

def chunks(lst, n):
    return [lst[i::n] for i in range(n)]

type_descr_unit = {
    'B83.W': ('Power', 'W'),
    'B81.W': ('Current', 'A'),
    'B81.L': ('Current', 'A'),
    'B82.W': ('Voltage', 'V'),
    'B84.W': ('Power Factor', ''),
}

def match_type(ctype):
    for tok in type_descr_unit:
        if tok in ctype:
            return type_descr_unit[tok]
    return (None, None)


def parse_side(cmdb_name):
    return {'R': 'A', 'L': 'B'}[cmdb_name[-1]]

async def getone(snmpEngine, hostname, name):
    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        snmpEngine,
        CommunityData('pdumon'),
        UdpTransportTarget(hostname, timeout=1.0, retries=4),
        ContextData(),
        *objs,
    )

    if errorIndication:
        #print(hostname[0], errorIndication)
        return
    elif errorStatus:
        #print('%s at %s' % (
        #    errorStatus.prettyPrint(),
        #    errorIndex), file=sys.stderr
        #)
        return
    else:
        ret = []
        i = 0
        ts = metricq.Timestamp.now()
        assert(len(varBinds)==len(counter_types))
        for bindName, val in varBinds:
            try:
                metric_name = "{}.{}".format(name, counter_types[i])
                ret.append((metric_name, ts, float(val) * multis[i]))
            except Exception as e:
                #print("Invalid result from %s: %s = %s" % (hostname, bindName, val), file=sys.stderr)
                return []
            i += 1
        return ret

async def collect_periodically(pdus, result_queue):
    snmpEngine = SnmpEngine()
    while True:
        get_data = []
        for rack in pdus:
           rackname = rack[1]
           for ip in rack[0]:
              get_data.append(getone(snmpEngine, (ip, 161), rackname))

        ret = await asyncio.gather(*get_data)
        #print("Worker putting {} PDU results into queue...".format(len(ret)))
        for r in ret:
           if r:
              result_queue.put_nowait(r)
        await asyncio.sleep(INTERVAL)


def do_work(input_queue, result_queue):
    pdus = input_queue.get()
    asyncio.run(collect_periodically(pdus, result_queue))

class PduSource(metricq.IntervalSource):
    def __init__(self, *args, **kwargs):
        logger.info("initializing PduSource")
        super().__init__(*args, **kwargs)
        self.period = None
        self.workers = None
        self.result_queue = mp.Queue()

    @metricq.rpc_handler('config')
    async def _on_config(self, rooms, **config):
        rate = 0.2
        self.period = 1 / rate

        # generate metrics from config structure:
        metrics = {}
        ip_by_rack = defaultdict(list)
        for room, racks_dict in rooms.items():
            for rack, pdus_dict in racks_dict.items():
                for pdu, pdu_attr in pdus_dict.items():
                    ip = pdu_attr['ip']
                    side = parse_side(pdu)
                    room_num = int(room[1:])
                    rack_num = int(rack[1:])
                    pdu_label = "{:02d}{:02d}{}".format(room_num, rack_num, side)
                    ip_by_rack[pdu_label].append(ip)
                    for ctype in counter_types:
                        metric = "LZR.E98.{}.{}".format(
                            pdu_label, ctype)
                        descr, unit = match_type(ctype)
                        if ctype[-1] in ["A", "B", "C", "D", "E", "F"]:
                            what = "Circuit {}".format(ctype[-1])
                        else:
                            what = "Phase {}".format(ctype[-1])
                        description = "Room {} Rack {} {} PDU {} {}".format(
                            room, rack, descr, side, what)
                        metrics[metric] = {
                            'rate': rate, 'description': description, 'unit': unit, 'room': room, 'rack': rack}

        if 'num_procs' in config:
            num_procs = config['num_procs']
        else:
            num_procs = mp.cpu_count()  # use all available cores

        chunked_racks = chunks(list(ip_by_rack.keys()), num_procs)
        work = mp.Queue()
        for part in chunked_racks:
            work.put([(ip_by_rack[rack], rack) for rack in part])

        print("Starting {} worker processes...".format(num_procs))
        sys.stdout.flush()
        
        if self.workers:  # kill old workers if _on_config gets called multiple times:
            self.workers.close()
            self.workers.terminate()

        original_sigint_handler = signal.signal(signal.SIGINT, orig_sig_handler)
        self.workers = mp.Pool(num_procs, do_work, (work, self.result_queue))
        signal.signal(signal.SIGINT, original_sigint_handler)
 
        #for signame in ["SIGINT", "SIGTERM"]:
        #   self.event_loop.add_signal_handler(getattr(signal, signame),
        #     functools.partial(self.on_signal, signame))
        
        print("Declaring {} metrics...".format(len(metrics)))
        await self.declare_metrics(metrics)

    async def update(self):
        send_metrics = []
        print(time.time(), self.result_queue.qsize())
        while True:
            try:
                result_list = self.result_queue.get_nowait()
                for metric_name, ts, value in result_list:
                   name = "LZR.E98.{}".format(metric_name)
                   print(name, ts, value)
                   send_metrics.append(self[name].send(ts, value))
            except Empty:
                break

        print(time.time(), "Count: {}".format(len(send_metrics)))
        if send_metrics:
           await asyncio.wait(send_metrics)
        print(time.time())


@click.command()
@click_log.simple_verbosity_option(logger)
def main():
    global orig_sig_handler
    orig_sig_handler = signal.getsignal(signal.SIGINT)

    src = PduSource(token=token, management_url=server)
    with aiomonitor.start_monitor(src.event_loop, locals={'src': src}):
       src.run() #catch_signals=())

if __name__ == "__main__":
    main()
