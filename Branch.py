import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

import grpc

import bank_pb2
import bank_pb2_grpc


class Branch(bank_pb2_grpc.BankSystemServicer):

    def __init__(self, id, balance, branches, bindAddress):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # the bind address for this branch
        self.bindAddress = bindAddress
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        self.writeSet = [0]
        # TODO: students are expected to store the processID of the branches
        pass

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self, request, context):
        print(datetime.now(), "Branch", self.id, "receive:", request.interface)
        sched = BackgroundScheduler()
        self.recvMsg.append("recv")
        if request.interface == "query":
            if self.checkWriteSet(request.writeSet):
                return bank_pb2.MsgDeliveryReply(
                    interface="query", result="success", money=str(self.balance))
            else:
                return bank_pb2.MsgDeliveryReply(interface="query", result="failed", money="null")

        elif request.interface == "deposit":
            if self.checkWriteSet(request.writeSet):
                self.writeSet.append(self.writeSet[-1] + 1)

                sched.add_job(lambda: self.propagate("propagate_deposit", request.money), 'date', run_date=datetime.today() + timedelta(seconds=1))
                # sched.add_job(self.test, 'date', run_date=datetime.today() + timedelta(seconds=1))
                sched.start()

                return bank_pb2.MsgDeliveryReply(
                    interface="deposit", result="success", money=str(self.deposit(int(request.money))))
            else:
                return bank_pb2.MsgDeliveryReply(interface="deposit", result="failed", money="null")

        elif request.interface == "withdraw":
            if self.checkWriteSet(request.writeSet):
                self.writeSet.append(self.writeSet[-1] + 1)

                return bank_pb2.MsgDeliveryReply(
                    interface="withdraw", result="success", money=str(self.withdraw(int(request.money))))
            else:
                return bank_pb2.MsgDeliveryReply(interface="withdraw", result="failed", money="null")

        elif request.interface == "propagate_deposit":
            self.writeSet = request.writeSet
            return bank_pb2.MsgDeliveryReply(
                interface="deposit", result="success", money=str(self.deposit(int(request.money))))

        elif request.interface == "propagate_withdraw":
            self.writeSet = request.writeSet
            return bank_pb2.MsgDeliveryReply(
                interface="withdraw", result="success", money=str(self.withdraw(int(request.money))))

    def checkWriteSet(self, writeSet):
        if writeSet == self.writeSet:
            return True

        return False

    def deposit(self, money):
        self.balance += money
        return self.balance

    def withdraw(self, money):
        self.balance -= money
        return self.balance

    def add_stub(self, address):
        self.stubList.append(bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address)))

    def propagate(self, interface, money):
        print(datetime.now(), "Branch", self.id, interface)
        for stub in self.stubList:
            stub.MsgDelivery(bank_pb2.MsgDeliveryRequest(
                interface=interface, money=money, writeSet=self.writeSet))

    def test(self):
        print("!!!")
