#!/usr/bin/python
import asyncio
import logging.handlers
import multiprocessing as mp
import queue
import sys
import threading
import time
import traceback
from collections import defaultdict
from collections.abc import Awaitable
from itertools import tee
from queue import Empty
from typing import Any, Mapping, Optional, Sequence

import click
import click_log  # type: ignore
import metricq
from metricq.logging import get_logger
from pysnmp.hlapi.asyncio import CommunityData  # type: ignore
from pysnmp.hlapi.asyncio import (
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
)

from .version import __version__  # noqa: F401 # magic import for automatic version

NaN = float("nan")

logger = get_logger("SnmpSource")
click_log.basic_config(logger)
# Use this if we ever use threads
# logger.handlers[0].formatter = logging.Formatter(fmt='%(asctime)s %(threadName)-16s %(levelname)-8s %(message)s')
logger.handlers[0].formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s"
)

Metric = str
DataPoint = tuple[Metric, metricq.Timestamp, float]
JsonDict = dict[str, Any]
Hostname = str
Community = str
HostnamePort = tuple[Hostname, int]
OID = str
ObjectConfig = tuple[Metric, float, int]
HostObjectConfig = dict[OID, ObjectConfig]
HostConfig = tuple[Hostname, Community, HostObjectConfig]


async def get_one(
    snmp_engine: SnmpEngine,
    host: HostnamePort,
    community: str,
    objects: HostObjectConfig,
) -> list[DataPoint]:
    """
    Get one SNMP object from a host and return a list of data points.
    """
    objs = [ObjectType(ObjectIdentity(obj_id)) for obj_id in objects.keys()]

    try:
        result: Awaitable[tuple[str, str, int, Sequence[Any]]] = await getCmd(
            snmp_engine,
            CommunityData(community),
            UdpTransportTarget(host, timeout=1.0, retries=3),
            ContextData(),
            *objs,
        )

        # yes, the duplicate await is intentional. For some reason, the getCmd
        # returns future. Hence we need another await to get the actual result.
        errorIndication, errorStatus, errorIndex, varBinds = await result

        ts = metricq.Timestamp.now()

        # also error handling of getCmd is a bit weird. It returns a tuple
        # with the error indication and the error status, but also raises exceptions
        if errorIndication:
            raise RuntimeError(f"SNMP engine error: {errorIndication}")

        if errorStatus:
            raise RuntimeError(
                f"SNMP device error: {errorStatus} at {objs[errorIndex - 1]}"
            )

    except Exception as e:
        # ts might not be defined here, if getCmd had raised an exception
        ts = metricq.Timestamp.now()
        logger.error(
            f"Failed to get from {host}: {str(e)}\n{''.join(traceback.format_exception(e))}"
        )
        return [(metric, ts, NaN) for metric, _, _ in objects.values()]

    assert len(varBinds) == len(objects)

    data_points: list[DataPoint] = []

    for bindName, val in varBinds:
        obj_id = f".{bindName}"
        try:
            metric, multiplier, _ = objects[obj_id]
            data_points.append((metric, ts, float(val) * multiplier))
        except KeyError as e:
            logger.error(
                f"Unexpected result for {host}, didn't requested that: {bindName} = {val}"
            )
        except Exception as e:
            logger.error(f"Invalid result for {host}: {bindName} = {val}: {e}")
            data_points.append((metric, ts, NaN))
    return data_points


async def collect_periodically(
    configurations: list[HostConfig],
    stop_event: threading.Event,
    result_queue: queue.Queue[list[DataPoint]],
    interval: float,
) -> None:
    snmp_engine = SnmpEngine()

    deadline = time.time()

    # stop_event will be set by the main process when it receives a SIGINT
    # or a reconfigure request.
    # while not stop_event.is_set():
    while True:
        deadline += interval

        while deadline < time.time():
            logger.warning("missed deadline")
            deadline += interval

        await asyncio.sleep(deadline - time.time())

        results = await asyncio.gather(
            *[
                get_one(snmp_engine, (host, 161), community, objects)
                for host, community, objects in configurations
            ]
        )

        for result in results:
            if result:
                result_queue.put_nowait(result)


async def start_collectors(
    host_config: list[HostConfig],
    stop_event: threading.Event,
    result_queue: queue.Queue[list[DataPoint]],
) -> None:
    """main work loop of worker processes

    This function is called by the multiprocessing workers.
    """
    grouped_host_configs: Mapping[float, list[HostConfig]] = defaultdict(list)

    for host, community, objects in host_config:
        grouped_by_interval: Mapping[float, HostObjectConfig] = defaultdict(dict)

        for id, config in objects.items():
            _, _, interval = config
            grouped_by_interval[interval][id] = config

        for object_interval, object_data in grouped_by_interval.items():
            grouped_host_configs[object_interval].append((host, community, object_data))

    await asyncio.gather(
        *[
            collect_periodically(host_configs, stop_event, result_queue, interval)
            for interval, host_configs in grouped_host_configs.items()
        ]
    )


def mp_worker(
    host_config: list[HostConfig],
    stop_event: threading.Event,
    result_queue: queue.Queue[list[DataPoint]],
) -> None:
    """init function of multiprocessing workers"""
    logger.debug("Starting worker process event loop")
    asyncio.run(start_collectors(host_config, stop_event, result_queue))
    logger.debug("Worker process exited event loop")


class SnmpSource(metricq.IntervalSource):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        logger.info("initializing SnmpSource")
        super().__init__(*args, **kwargs)
        self.workers: Optional[mp.pool.Pool] = None
        manager = mp.Manager()
        self.result_queue: queue.Queue[list[DataPoint]] = manager.Queue()
        self.stop_event: threading.Event = manager.Event()

    @metricq.rpc_handler("config")
    async def _on_config(
        self,
        default_community: Community,
        default_interval: int,
        default_prefix: str,
        default_object_collections: list[str],
        additional_metric_attributes: list[str],
        snmp_object_collections: JsonDict,
        **config: Any,
    ) -> None:
        self.period = metricq.Timedelta.from_s(1)
        metrics_metadata: dict[Hostname, JsonDict] = {}

        # key: ip, data: [{OID: (metric-name, multiplier, interval)}, ...]
        objects_by_host: dict[Hostname, HostObjectConfig] = defaultdict(dict)
        community_by_host: dict[Hostname, Community] = {}

        for host, host_config in config["hosts"].items():
            community_by_host[host] = host_config.get("community", default_community)

            default_host_interval = host_config.get("interval", default_interval)

            objects = {}
            for obj_col in host_config.get("objects", default_object_collections):
                objects.update(snmp_object_collections[obj_col])

            for oid, object in objects.items():
                metric = "{}.{}.{}".format(
                    default_prefix, host_config["infix"], object["suffix"]
                )

                description = "{} {}".format(
                    host_config["description"], object["short_description"]
                )

                interval = object.get("interval", default_host_interval)

                metadata = {
                    "rate": 1.0 / interval,
                    "description": description,
                }

                for attribute in additional_metric_attributes:
                    if attribute in object:
                        metadata[attribute] = object[attribute]
                    elif attribute in host_config:
                        metadata[attribute] = host_config[attribute]

                metrics_metadata[metric] = metadata

                objects_by_host[host][oid] = (
                    metric,
                    object.get("multiplier", 1.0),
                    interval,
                )

        num_procs = min(config.get("num_procs", mp.cpu_count()), len(objects_by_host))

        logger.info("Starting {} worker processes...".format(num_procs))
        sys.stdout.flush()

        # kill old workers for reconfiguration
        if self.workers:
            # send stop event to workers
            self.stop_event.set()

            # kill workers and wait for them to exit
            self.workers.close()
            self.workers.terminate()
            self.workers.join()

            # reset stop event
            self.stop_event.clear()

        # start new workers and let them inherit the stop event and the result queue
        # also use the "spawn" context instead of fork to avoid problems with
        # deadlocks in the multiprocessing signal handling
        self.workers = mp.get_context("spawn").Pool(
            num_procs, initargs=(self.stop_event, self.result_queue)
        )

        # distribute host configurations to workers
        for chunk in tee(objects_by_host.keys(), num_procs):
            self.workers.apply_async(
                mp_worker,
                (
                    [
                        (host, community_by_host[host], objects_by_host[host])
                        for host in chunk
                    ],
                    self.stop_event,
                    self.result_queue,
                ),
                error_callback=lambda e: logger.error(
                    "Exception in worker: {}".format(e)
                ),
            )

        logger.info("Declaring {} metrics...".format(len(metrics_metadata)))
        await self.declare_metrics(metrics_metadata)

    async def update(self) -> None:
        send_metric_count = 0
        while True:
            try:
                result_list = self.result_queue.get_nowait()
                for metric_name, ts, value in result_list:
                    self[metric_name].append(ts, value)
                    send_metric_count += 1
            except Empty:
                break
        ts_before = time.time()
        try:
            await self.flush()
        except Exception as e:
            logger.error("Exception in send: {}".format(str(e)))
        logger.info(
            "Send took {:.2f} seconds, count: {}".format(
                time.time() - ts_before, send_metric_count
            )
        )

    def on_signal(self, signal: str) -> None:
        try:
            logger.info("Received signal {}".format(signal))
            if self.workers:
                logger.info("Terminating worker processes...")
                self.stop_event.set()
                self.workers.close()
                self.workers.terminate()
                self.workers.join()
                logger.info("Worker processes terminated.")
        except Exception as e:
            logger.error("Exception in on_signal: {}".format(str(e)))
        finally:
            super().on_signal(signal)


@click.command()
@click.option("--server", default="amqp://localhost/")
@click.option("--token", default="source-py-snmp")
@click_log.simple_verbosity_option(logger)  # type: ignore
def run(server: str, token: str) -> None:
    src = SnmpSource(token=token, management_url=server)
    src.run()


if __name__ == "__main__":
    run()
