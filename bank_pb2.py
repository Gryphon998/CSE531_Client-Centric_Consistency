# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: bank.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nbank.proto\x12\x1a\x63lient_centric_consistency\"H\n\x12MsgDeliveryRequest\x12\x11\n\tinterface\x18\x01 \x01(\t\x12\r\n\x05money\x18\x02 \x01(\t\x12\x10\n\x08writeSet\x18\x03 \x03(\x03\"D\n\x10MsgDeliveryReply\x12\x11\n\tinterface\x18\x01 \x01(\t\x12\x0e\n\x06result\x18\x02 \x01(\t\x12\r\n\x05money\x18\x03 \x01(\t2{\n\nBankSystem\x12m\n\x0bMsgDelivery\x12..client_centric_consistency.MsgDeliveryRequest\x1a,.client_centric_consistency.MsgDeliveryReply\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bank_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _MSGDELIVERYREQUEST._serialized_start=42
  _MSGDELIVERYREQUEST._serialized_end=114
  _MSGDELIVERYREPLY._serialized_start=116
  _MSGDELIVERYREPLY._serialized_end=184
  _BANKSYSTEM._serialized_start=186
  _BANKSYSTEM._serialized_end=309
# @@protoc_insertion_point(module_scope)
