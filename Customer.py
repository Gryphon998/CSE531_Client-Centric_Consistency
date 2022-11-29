from datetime import datetime
from time import sleep

import grpc

import bank_pb2
import bank_pb2_grpc
from google.protobuf.json_format import MessageToDict


class Customer:
    def __init__(self, id, events, address_map):
        # unique ID of the Customer
        self.id = id
        # events from the input
        self.events = events
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # pointer for the stub
        self.stub_map = self.createStubMap(address_map)
        #write set
        self.writeSet = [0]

    # TODO: students are expected to create the Customer stub
    def createStubMap(self, address_map):
        stub_map = {}
        for key in address_map:
            stub_map[key] = bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address_map.get(key)))
        return stub_map

    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        for event in self.events:
            dest = event["dest"]
            interface = event["interface"]
            money = str(event.get("money", "0"))
            print(datetime.now(), "Client", self.id, "send:", interface, self.writeSet)
            reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(
                interface=interface, money=money, writeSet=self.writeSet))

            print(datetime.now(), "Client", self.id, "receive:", reply.interface, reply.result)
            while reply.result == "failed":
                sleep(0.3)
                print(interface + "retry")
                reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(
                    interface=interface, money=money, writeSet=self.writeSet))

            self.writeSet.append(self.writeSet[-1] + 1)
            msg = MessageToDict(reply)

            # if interface == "deposit" or interface == "withdraw":
            #     del msg['money']

            self.recvMsg.append(msg)

        return {"id": self.id, "recv": self.recvMsg}
