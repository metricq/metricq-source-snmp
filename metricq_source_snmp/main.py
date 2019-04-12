#!/usr/bin/python

import asyncio
import time
import sys
from collections import defaultdict
import multiprocessing as mp
from queue import Empty
import logging
import signal
import click
import click_log
import aiomonitor
import metricq
from pysnmp.hlapi.asyncio import getCmd, ObjectType, ObjectIdentity, CommunityData, ContextData, SnmpEngine
from metricq.logging import get_logger
from config import server, token

INTERVAL = 5

logger = get_logger()
click_log.basic_config(logger)
logger.setLevel('ERROR')
# Use this if we ever use threads
# logger.handlers[0].formatter = logging.Formatter(fmt='%(asctime)s %(threadName)-16s %(levelname)-8s %(message)s')
logger.handlers[0].formatter = logging.Formatter(
    fmt='%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s')
orig_sig_handler = None


async def getone(snmp_engine, host, community_string, objects):
    objs = [ObjectType(ObjectIdentity(obj_id)) for obj_id in objects.keys()]

    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        snmp_engine,
        CommunityData(community_string),
        UdpTransportTarget(host, timeout=1.0, retries=4),
        ContextData(),
        *objs,
    )

    if errorIndication:
        #print(host, errorIndication)
        return
    elif errorStatus:
        # print('%s at %s' % (
        #    errorStatus.prettyPrint(),
        #    errorIndex), file=sys.stderr
        # )
        return
    else:
        ret = []
        ts = metricq.Timestamp.now()

        assert(len(varBinds) == len(objects))

        for bindName, val in varBinds:
            obj_id = ".{}".format(bindName)  # add "." in front
            try:
                metric_name, multi, interval = objects[obj_id]
                ret.append((metric_name, ts, float(val) * multi))
            except Exception as e:
                #print("Invalid result from %s: %s = %s" % (host, bindName, val), file=sys.stderr)
                return []
        return ret


async def collect_periodically(work, result_queue):
    snmp_engine = SnmpEngine()
    while True:
        get_data = []
        for host, community_string, objects in work:
            get_data.append(getone(snmp_engine, (host, 161),
                                   community_string, objects))

        ret = await asyncio.gather(*get_data)
        #print("Worker putting {} PDU results into queue...".format(len(ret)))
        for r in ret:
            if r:
                result_queue.put_nowait(r)
        await asyncio.sleep(INTERVAL)


def do_work(input_queue, result_queue):
    """init function of multiprocessing workers"""
    work = input_queue.get()
    asyncio.run(collect_periodically(work, result_queue))


def chunks(lst, n):
    return [lst[i::n] for i in range(n)]


class PduSource(metricq.IntervalSource):
    def __init__(self, *args, **kwargs):
        logger.info("initializing PduSource")
        super().__init__(*args, **kwargs)
        self.period = None
        self.workers = None
        self.result_queue = mp.Queue()

    @metricq.rpc_handler('config')
    async def _on_config(self, default_community, default_interval, default_prefix, default_object_collections,
                         additional_metric_attributes, snmp_object_collections, **config):
        rate = 0.2
        self.period = 1 / rate

        metrics = {}  # holds metrics for declaration to metricq

        # key: ip, data: [(OID, metric-name, multi, interval), ...]
        objects_by_host = defaultdict(dict)
        community_by_host = {}

        for host, host_cfg in config['hosts'].items():
            community_by_host[host] = host_cfg.get(
                'community', default_community)

            objs = {}
            obj_col_list = host_cfg.get('objects', default_object_collections)
            for obj_col in obj_col_list:
                objs.update(snmp_object_collections[obj_col])

            for obj_id, obj in objs.items():
                description = "{} {}".format(
                    host_cfg['description'], obj['short_description'])
                metric_name = "{}.{}.{}".format(
                    default_prefix, host_cfg['infix'], obj['suffix'])
                metric = {'rate': rate, 'description': description}
                for metric_attr in additional_metric_attributes:
                    if metric_attr in obj:
                        metric[metric_attr] = obj[metric_attr]
                    elif metric_attr in host_cfg:
                        metric[metric_attr] = host_cfg[metric_attr]
                metrics[metric_name] = metric

                interval = obj.get('interval', default_interval)
                multi = obj.get('multiplier', 1.0)

                objects_by_host[host][obj_id] = (metric_name, multi, interval)

        num_procs = config.get('num_procs', mp.cpu_count())

        chunked = chunks(list(objects_by_host.keys()), num_procs)
        work = mp.Queue()
        for part in chunked:
            work.put([(host, community_by_host[host], objects_by_host[host])
                      for host in part])

        print("Starting {} worker processes...".format(num_procs))
        sys.stdout.flush()

        if self.workers:  # kill old workers if _on_config gets called multiple times:
            self.workers.close()
            self.workers.terminate()

        original_sigint_handler = signal.signal(
            signal.SIGINT, orig_sig_handler)
        self.workers = mp.Pool(num_procs, do_work, (work, self.result_queue))
        signal.signal(signal.SIGINT, original_sigint_handler)

        # for signame in ["SIGINT", "SIGTERM"]:
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
        src.run()  # catch_signals=())


if __name__ == "__main__":
    main()
