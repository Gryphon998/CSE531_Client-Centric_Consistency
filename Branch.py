from datetime import datetime, timedelta
import logging

import grpc
from apscheduler.schedulers.background import BackgroundScheduler

import bank_pb2
import bank_pb2_grpc

_LOGGER = logging.getLogger(__name__)


class Branch(bank_pb2_grpc.BankSystemServicer):

    def __init__(self, id, balance, bind_address):
        # unique ID of the branch
        self.id = id
        # replica of the branch's balance
        self.balance = balance
        # the bind address for this branch
        self.bind_address = bind_address
        # the list of client stubs to communicate with this branch
        self.stubList = list()
        # a set of writes from customer
        self.writeSet = [0]

    def MsgDelivery(self, request, context):
        """
        Handle received messages from other branches or customers.
        :param request: a gRPC request from a branch or customer
        :param context: gRPC protocol required context
        """
        _LOGGER.info("Branch", self.id, "receive:", request.interface)
        sched = BackgroundScheduler()

        if request.interface == "query":
            # Handle "query" requests from customers
            if self.writeSet == request.writeSet:
                return bank_pb2.MsgDeliveryReply(
                    interface="query", result="success", money=str(self.balance))
            else:
                return bank_pb2.MsgDeliveryReply(interface="query", result="failed", money="null")
        elif request.interface == "deposit":
            # Handle "deposit" requests from customers
            if self.writeSet == request.writeSet:
                self.writeSet.append(self.writeSet[-1] + 1)
                sched.add_job(lambda: self.propagate("propagate_deposit", request.money), 'date',
                              run_date=datetime.today() + timedelta(seconds=1))
                sched.start()

                return bank_pb2.MsgDeliveryReply(
                    interface="deposit", result="success", money=str(self.deposit(int(request.money))))
            else:
                return bank_pb2.MsgDeliveryReply(interface="deposit", result="failed", money="null")
        elif request.interface == "withdraw":
            # Handle "withdraw" requests from customers
            if self.writeSet == request.writeSet:
                self.writeSet.append(self.writeSet[-1] + 1)

                return bank_pb2.MsgDeliveryReply(
                    interface="withdraw", result="success", money=str(self.withdraw(int(request.money))))
            else:
                return bank_pb2.MsgDeliveryReply(interface="withdraw", result="failed", money="null")
        elif request.interface == "propagate_deposit":
            # Handle propagated "deposit" requests from other branches
            self.writeSet = request.writeSet
            return bank_pb2.MsgDeliveryReply(
                interface="deposit", result="success", money=str(self.deposit(int(request.money))))
        elif request.interface == "propagate_withdraw":
            # Handle propagated "withdraw" requests from other branches
            self.writeSet = request.writeSet
            return bank_pb2.MsgDeliveryReply(
                interface="withdraw", result="success", money=str(self.withdraw(int(request.money))))

    def deposit(self, money):
        self.balance += money
        return self.balance

    def withdraw(self, money):
        self.balance -= money
        return self.balance

    def add_stub(self, address):
        self.stubList.append(bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address)))

    def propagate(self, interface, money):
        _LOGGER.info(datetime.now(), "Branch", self.id, interface)
        for stub in self.stubList:
            stub.MsgDelivery(bank_pb2.MsgDeliveryRequest(
                interface=interface, money=money, writeSet=self.writeSet))
