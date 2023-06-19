import json
import logging
import multiprocessing
import socket
import sys
import time
from concurrent import futures

import grpc

import bank_pb2_grpc
from Branch import Branch
from Customer import Customer

_LOGGER = logging.getLogger(__name__)
_PROCESS_COUNT = multiprocessing.cpu_count()
_THREAD_CONCURRENCY = _PROCESS_COUNT

address_map = {}
workers = []
branches = []


def _reserve_port():
    """Find a free port at localhost"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    return sock.getsockname()[1]


def _run_server(branch):
    """"Start a branch serve in a subprocess with the passed in branch information."""
    _LOGGER.info("Initialize new branch @ %s - id: %d, balance: %d ", branch.bind_address, branch.id, branch.balance)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_THREAD_CONCURRENCY))
    bank_pb2_grpc.add_BankSystemServicer_to_server(branch, server)
    server.add_insecure_port(branch.bind_address)
    server.start()
    server.wait_for_termination()


def _run_client(customer):
    """Start a customer serve with the passed in customer information."""
    _LOGGER.info("Initialize a new customer - id: %d.", customer.id)
    _LOGGER.info(customer.executeEvents())


def branches_init(processes):
    """
    Init branches based on the information of input json.
    :param processes: processes recorded in json file
    """
    for process in processes:
        if process["type"] == "branch":
            new_branch = Branch(process["id"], process["balance"], 'localhost:{}'.format(_reserve_port()))
            address_map[new_branch.id] = new_branch.bind_address
            branches.append(new_branch)

    # Add all other branches' addresses to a branch.
    for branch in branches:
        for id, address in address_map.items():
            if branch.id != id:
                branch.add_stub(address)

        worker = multiprocessing.Process(target=_run_server, args=(branch,))
        worker.start()
        workers.append(worker)


def customer_init(processes):
    """
    Init customers based on the information of input json.
    :param processes: processes recorded in json file
    """
    for process in processes:
        if process["type"] == "customer":
            new_customer = Customer(process["id"], process["events"], address_map)
            worker = multiprocessing.Process(target=_run_client, args=(new_customer,))
            worker.start()
            workers.append(worker)


if __name__ == '__main__':
    # handler = logging.FileHandler('output.log', 'w+')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[PID %(process)d] %(message)s')
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)

    f = open(sys.argv[1])
    input_json = json.load(f)

    # Parse input json to initialize branches and customers with 1 second interval.
    branches_init(input_json)
    time.sleep(1)
    customer_init(input_json)

    for worker in workers:
        worker.join()

    f.close()
