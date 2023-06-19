import logging
from time import sleep

import grpc
from google.protobuf.json_format import MessageToDict

import bank_pb2
import bank_pb2_grpc

_LOGGER = logging.getLogger(__name__)


def createStubMap(address_map):
    stub_map = {}
    for stub in address_map:
        stub_map[stub] = bank_pb2_grpc.BankSystemStub(grpc.insecure_channel(address_map.get(stub)))
    return stub_map


class Customer:
    def __init__(self, id, events, address_map):
        # unique ID of the customer
        self.id = id
        # events from the input json
        self.events = events
        # pointer for the stub
        self.stub_map = createStubMap(address_map)
        # a set of writes from the customer
        self.writeSet = [0]
        # a list of received messages used for logging purpose
        self.recvMsg = list()

    def executeEvents(self):
        """Execute the event from input json."""
        for event in self.events:
            dest = event["dest"]
            interface = event["interface"]
            money = str(event.get("money", "0"))
            _LOGGER.info("Client", self.id, "send:", interface, self.writeSet)
            reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(
                interface=interface, money=money, writeSet=self.writeSet))

            _LOGGER.info("Client", self.id, "- receive", reply.interface, reply.result)
            while reply.result == "failed":
                sleep(0.3)
                _LOGGER.info(interface, "retry...")
                reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(
                    interface=interface, money=money, writeSet=self.writeSet))

            self.writeSet.append(self.writeSet[-1] + 1)

            msg = MessageToDict(reply)
            self.recvMsg.append(msg)

        return {"id": self.id, "recv": self.recvMsg}
