import grpc

import bank_pb2
import bank_pb2_grpc
from google.protobuf.json_format import MessageToDict


class Customer:
    def __init__(self, id, events, address):
        # unique ID of the Customer
        self.id = id
        # events from the input
        self.events = events
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # pointer for the stub
        self.stub = self.createStub(address)

    # TODO: students are expected to create the Customer stub
    def createStub(self, address):
        return bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address))

    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        for event in self.events:
            id = event["id"]
            interface = event["interface"]
            money = event["money"]
            msg = MessageToDict(self.stub.MsgDelivery(bank_pb2.MsgDeliveryRequest(id=id, interface=interface, money=money)))

            if interface == "deposit" or interface == "withdraw":
                del msg['money']

            self.recvMsg.append(msg)

        return {"id": self.id, "recv": self.recvMsg}
