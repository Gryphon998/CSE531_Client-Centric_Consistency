from time import sleep

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
        # iterate the processID of the branches
        # TODO: students are expected to store the processID of the branches
        pass

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self, request, context):
        self.recvMsg.append("recv")
        if request.interface == "query":
            sleep(3)
            return bank_pb2.MsgDeliveryReply(
                interface="query", result="success", money=self.balance)
        elif request.interface == "deposit":
            return bank_pb2.MsgDeliveryReply(
                interface="deposit", result="success", money=self.deposit(request.money, True))
        elif request.interface == "withdraw":
            return bank_pb2.MsgDeliveryReply(
                interface="withdraw", result="success", money=self.withdraw(request.money, True))
        elif request.interface == "propogate_deposit":
            return bank_pb2.MsgDeliveryReply(
                interface="deposit", result="success", money=self.deposit(request.money, False))
        elif request.interface == "propogate_withdraw":
            return bank_pb2.MsgDeliveryReply(
                interface="withdraw", result="success", money=self.withdraw(request.money, False))

    def deposit(self, money, propogate):
        self.balance += money

        if propogate:
            for stub in self.stubList:
                stub.MsgDelivery(bank_pb2.MsgDeliveryRequest(
                    id=self.id, interface="propogate_deposit", money=money))

        return self.balance

    def withdraw(self, money, propogate):
        self.balance -= money

        if propogate:
            for stub in self.stubList:
                stub.MsgDelivery(bank_pb2.MsgDeliveryRequest(
                    id=self.id, interface="propogate_withdraw", money=money))

        return self.balance

    def add_stub(self, address):
        self.stubList.append(bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address)))