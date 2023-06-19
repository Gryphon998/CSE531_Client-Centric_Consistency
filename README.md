# Client-Centric Consistency

## Problem Statement
### Set Maintenance
To ensure the proper functioning of both monotonic write and read-your-write operations, it is crucial to maintain equivalent write sets between customers and different branches. We need to establish an effective method for synchronizing the write set between customers and branches during message exchange.

The approach in this project is to provide the same initial write set to both customers and branches during the initialization phase. Branches only execute requests when the write set in the request matches their own write set. Upon successful execution, the branch responds with a successful reply and increases its write set. Similarly, the customer increases its write set only upon receiving a successful reply.

### Handling Write Set Mismatch
During various requests with different interface types, there may be scenarios where the write sets do not match. In such cases, it is important to determine the ideal approach for handling these situations. Should the request be suspended on the branch side until the write sets match, returning a successful reply, or should a failed reply be returned and let the customer decide the next course of action?

To avoid blocking the customer, the branch will provide a failed reply when encountering a mismatched write set. The customer will then wait for a certain interval and retry sending the request.

### Simulation of Propagation Delay
Since the entire project is implemented on a single machine with multiple processing architectures, the propagation requests between branches have negligible delay. Therefore, what is the best practice for simulating a delay that can manually create mismatched write sets between customers and branches?

After conducting research, I found that utilizing a background scheduler is an effective method to introduce delay in the propagation request within the gRPC endpoint "MsgDelivery."

### Verification of Events Sequence
Assuming we have successfully simulated propagation delay, what kind of logs or output can provide us with the best observations for analyzing both monotonic write and read-your-write operations when write set mismatches occur?

To obtain detailed event logs, I use print logs with a fixed format to trace the sequence of different requests and replies. This allows us to verify the implementation of both monotonic write and read-your-write operations.

## Implementation
### Customer
``` python
reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(interface=interface, money=money, writeSet=self.writeSet))

# Keep sending request to target branch with 300ms interval if reply is failed
while reply.result == "failed":
  sleep(0.3)
  reply = self.stub_map[dest].MsgDelivery(bank_pb2.MsgDeliveryRequest(
  interface=interface, money=money, writeSet=self.writeSet))
```
By default, send a request to the target branch and parse the reply. If the reply is successful, proceed to the next code block. If not, enter a while loop and continue sending requests to the target branch at a 300ms interval.

``` python
if interface == "deposit" or interface == "withdraw":
  # Only increase write set for successful deposit and withdraw
  self.writeSet.append(self.writeSet[-1] + 1)
```
Customers only increase the write set for successful deposit and withdraw replies.

``` python
if interface == "query":
  # Log balance when do a query
  self.recvMsg.append({"id": self.id, "balance": reply.money})
```
Create a custom dictionary to match the output example.

### Branch
``` python
if request.interface == "query":
  # Only do query when write sets are matched
  if self.writeSet == request.writeSet:
    return bank_pb2.MsgDeliveryReply(
    interface="query", result="success", money=str(self.balance))
  else:
    return bank_pb2.MsgDeliveryReply(interface="query", result="failed", money="0")
```
For query requests, only check the write set but do not increase the Branch’s write
set.

``` python
elif request.interface == "deposit":
  # Only do deposit when write sets are matched
  if self.writeSet == request.writeSet:
    # Update write set when execute the request
    self.writeSet.append(self.writeSet[-1] + 1)
    # Delay 1 second to send propagate request
    sched.add_job(lambda: self.propagate("propagate_deposit", request.money), 'date',
    run_date=datetime.now() + timedelta(seconds=1))
    sched.start()
  
    return bank_pb2.MsgDeliveryReply(interface="deposit", result="success", money=str(self.deposit(int(request.money))))
 else:
   return bank_pb2.MsgDeliveryReply(interface="deposit", result="failed", money="0")
```
To process a deposit, first compare the local write set with the incoming one. If they do not match, return a failed reply to the customer. If they match, update the local write set, schedule a propagation job with a delay of 1 second to simulate the propagation delay between branches, perform the deposit operation to increase the balance, and finally return a successful reply to the customer.

The process for a withdrawal is similar to that of a deposit.

## Analysis
### Monotonic Write
```
[2022-11-30 01:44:00.412] Client(1) ---> Branch(1): intf(deposit), money(400), writeSet([0])
[2022-11-30 01:44:00.415] Branch(1): Receive Client request which matches current writeSet([0])
[2022-11-30 01:44:00.418] Branch(1): Execute Client request and update current writeSet to [0, 1]
[2022-11-30 01:44:00.452] Branch(1) ---> Client(1): intf(deposit), money(400), result(success)
[2022-11-30 01:44:00.452] Client(1): Receive successful reply and update current writeSet to [0, 1]
[2022-11-30 01:44:00.452] Client(1) ---> Branch(2): intf(withdraw), money(400), writeSet([0, 1])
[2022-11-30 01:44:00.454] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 01:44:00.457] Branch(2) ---> Client(1): intf(withdraw), money(0), result(failed)
[2022-11-30 01:44:00.457] Client(1): Sleep 300ms and retry
[2022-11-30 01:44:00.757] Client(1) ---> Branch(2): intf(withdraw), money(400), writeSet([0, 1])
[2022-11-30 01:44:00.758] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 01:44:00.758] Branch(2) ---> Client(1): intf(withdraw), money(0), result(failed)
[2022-11-30 01:44:00.758] Client(1): Sleep 300ms and retry
[2022-11-30 01:44:01.059] Client(1) ---> Branch(2): intf(withdraw), money(400), writeSet([0, 1])
[2022-11-30 01:44:01.059] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 01:44:01.059] Branch(2) ---> Client(1): intf(withdraw), money(0), result(failed)
[2022-11-30 01:44:01.059] Client(1): Sleep 300ms and retry
[2022-11-30 01:44:01.359] Client(1) ---> Branch(2): intf(withdraw), money(400), writeSet([0, 1])
[2022-11-30 01:44:01.360] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 01:44:01.360] Branch(2) ---> Client(1): intf(withdraw), money(0), result(failed)
[2022-11-30 01:44:01.360] Client(1): Sleep 300ms and retry
[2022-11-30 01:44:01.421] Branch(2): Receive Branch propagate request and update current writeSet to [0, 1]
[2022-11-30 01:44:01.661] Client(1) ---> Branch(2): intf(withdraw), money(400), writeSet([0, 1])
[2022-11-30 01:44:01.661] Branch(2): Receive Client request which matches current writeSet([0, 1])
[2022-11-30 01:44:01.662] Branch(2): Execute Client request and update current writeSet to [0, 1, 2]
[2022-11-30 01:44:01.696] Branch(2) ---> Client(1): intf(withdraw), money(0), result(success)
[2022-11-30 01:44:01.696] Client(1): Receive successful reply and update current writeSet to [0, 1, 2]
[2022-11-30 01:44:01.696] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1, 2])
[2022-11-30 01:44:01.696] Branch(2): Receive Client request which matches current writeSet([0, 1, 2])
[2022-11-30 01:44:01.696] Branch(2) ---> Client(1): intf(query), money(0), result(success)
[2022-11-30 01:44:02.664] Branch(1): Receive Branch propagate request and update current writeSet to [0, 1, 2]
```
* The customer initiates a deposit request to Branch 1 with an initial write set of [0].
* Branch 1 verifies that the write sets match, updates its write set to [0, 1], processes the deposit operation, increases the balance to 400, returns a successful reply to the customer, and schedules a propagate request to Branch 2 after a 1-second delay.
* The customer receives the successful reply, updates its write set to [0, 1], and proceeds.
* The customer sends a withdrawal request to Branch 2 with a write set of [0, 1].
* Branch 2 detects a write set mismatch and returns a failed reply.
* The customer receives the failed reply, waits for 300ms, and resends the request to Branch 2.
* Despite multiple retries, the request fails. However, during one of the retries, Branch 2 receives the propagate request from Branch 1, updates its write set to [0, 1], and adjusts its balance to 400.
* Branch 2 receives the subsequent retry request, verifies the write sets match, updates its write set to [0, 1, 2], processes the withdrawal operation, reduces the balance to 0, returns a successful reply to the customer, and schedules a propagate request to Branch 1 after a 1-second delay.
* The customer receives the successful reply, updates its write set to [0, 1, 2], and continues.
* The customer sends a query request to Branch 2 with a write set of [0, 1, 2].
* Branch 2 receives the request, verifies the write sets match, and replies with an expected balance of 0.
* After a 1-second delay, Branch 1 receives the propagate request from Branch 2.

### Read Your Write
```
[2022-11-30 00:40:20.815] Client(1) ---> Branch(1): intf(deposit), money(400), writeSet([0])
[2022-11-30 00:40:20.817] Branch(1): Receive Client request which matches current writeSet([0])
[2022-11-30 00:40:20.820] Branch(1): Execute Client request and update current writeSet to [0, 1]
[2022-11-30 00:40:20.854] Branch(1) ---> Client(1): intf(deposit), money(400), result(success)
[2022-11-30 00:40:20.854] Client(1): Receive successful reply and update current writeSet to [0, 1]
[2022-11-30 00:40:20.854] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1])
[2022-11-30 00:40:20.856] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 00:40:20.859] Branch(2) ---> Client(1): intf(query), money(0), result(failed)
[2022-11-30 00:40:20.859] Client(1): Sleep 300ms and retry
[2022-11-30 00:40:21.160] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1])
[2022-11-30 00:40:21.160] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 00:40:21.160] Branch(2) ---> Client(1): intf(query), money(0), result(failed)
[2022-11-30 00:40:21.160] Client(1): Sleep 300ms and retry
[2022-11-30 00:40:21.461] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1])
[2022-11-30 00:40:21.462] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 00:40:21.462] Branch(2) ---> Client(1): intf(query), money(0), result(failed)
[2022-11-30 00:40:21.462] Client(1): Sleep 300ms and retry
[2022-11-30 00:40:21.762] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1])
[2022-11-30 00:40:21.763] Branch(2): Receive Client request which does NOT match current writeSet([0])
[2022-11-30 00:40:21.763] Branch(2) ---> Client(1): intf(query), money(0), result(failed)
[2022-11-30 00:40:21.763] Client(1): Sleep 300ms and retry
[2022-11-30 00:40:21.824] Branch(2): Receive Branch propagate request and update current writeSet to [0, 1]
[2022-11-30 00:40:22.064] Client(1) ---> Branch(2): intf(query), money(0), writeSet([0, 1])
[2022-11-30 00:40:22.064] Branch(2): Receive Client request which matches current writeSet([0, 1])
[2022-11-30 00:40:22.064] Branch(2) ---> Client(1): intf(query), money(400), result(success)
```
* The customer initiates a deposit request to Branch 1 with an initial write set of [0].
* Branch 1 verifies that the write sets match, updates its write set to [0, 1], processes the deposit operation, increases the balance to 400, returns a successful reply to the customer, and schedules a propagate request to Branch 2 after a 1-second delay.
* The customer receives the successful reply and updates its write set to [0, 1].
* The customer sends a query request to Branch 2 with a write set of [0, 1].
* Branch 2 detects a write set mismatch and returns a failed reply.
* The customer receives the failed reply, sleeps for 300ms, and resends the request to Branch 2.
* Despite multiple retries, the request fails. However, during one of the retries, Branch 2 receives the propagate request from Branch 1, updates its write set to [0, 1], and adjusts its balance.
* Branch 2 receives the subsequent retry request, verifies the write sets match, and replies with the expected balance of 400.

## Requirements
### Purpose
The goal of this project is to implement the client-centric consistency model. The job is to implement the essential functions that enforce the client-centric consistency, specifically Monotonic Write consistency and Read your Write consistency of the replicated data in the bank.
<p align="center">
  <img src="https://github.com/Gryphon998/CSE531_Client-Centric_Consistency/assets/41406456/cd69d0fe-0e91-437b-a52b-0bc30fae78a6">
</p>

### Objectives
* Implement the essential functions that enforces the client-centric consistency.
* Enforce the Monotonic Write policy, which extends the implementation of previous interfaces.
* Enforce the Read your Write policy, which extends the implementation of previous interfaces.

### Description
The customer described in (1) of diagram A, accesses the banking system by connecting to one of the replicas in a transparent way. In other words, the application running on the customer’s mobile device is unaware of which replica it is actually using. Assume the customer performs several update operations and then disconnects. Later the customer accesses the banking system again possibly after removing to a different location or using a different access device. At that point the customer may be connected to a different replica than before as shown in (2), (3) of Diagram A. However if the updates performed previously have not yet been propagated, the customer will notice inconsistent behavior. In particular, the customer would expect to see all previously made changes, but instead it appears as if nothing at all has happened. This problem can be alleviated by introducing client-centric consistency. In essence, client-centric consistency
provides guarantees for a single client concerning the consistency of accesses to a data store by that client.

#### Monotonic Writes
In many situations, it is important that write operations are propagated in the correct order to all copies of the data store. This property is expressed in monotonic-write consistency. In a monotonic-write consistency store, the following condition holds: A write operation by a process on a data item x is completed before any successive write operation on x by the same process. Suppose that a client has an empty bank account and deposits $100 in location A. Suppose that the customer also withdraws while in location B. How and when the deposit of $100 in location A will be transferred to location B is left unspecified. In this case, if the deposit request has not yet been received by the server in location B, then the withdrawal request will fail.

#### Read your Writes
A data store is said to provide read-your-writes consistency, if the following condition holds: The effect of a write operation by a process on data item x will always be seen by a successive read operation on x by the same process. Suppose the customer deposits $100 in an empty bank account, and is planning to first check the bank account has $100 and then withdraw $100. The customer issues sequential order of requests (deposit -> query -> withdrawal) to the server. The customer may fail to withdraw the money from the bank because the query request can return $0. This annoying problem arises because the query request contacted a replication which the new deposit request had not yet propagated.

### Input and output
The input file contains one Customer and multiple Branch processes. The format of the input file follows Project 1, you will be using the destination parameter “dest” which has a value of a unique identifier of some branch.

#### Input format
```
[ // array of processes
 { // Customer process #1
  "id" : {a unique identifier of a customer or a branch},
  "type" : "customer",
  "events" :
    [
     {
      "interface" : {query | deposit | withdraw},
      "money" : {an integer value},
      "id" : {unique identifier of an event},
      "dest" : {a unique identifier of the branch}
     }
    ]
 }
 { // Branch process #1
  "id" : {a unique identifier of a customer or a branch},
  "type" : "branch"
  "balance" : {replica of the amount of money stored in the branch}
 }
 { … } // Branch process #2
 { … } // Branch process #3
 { … } // Branch process #N
]
```
