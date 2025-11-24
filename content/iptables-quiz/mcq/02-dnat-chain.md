---
id: iptables-02-dnat-chain
day: 1
tags: [iptables, nat, dnat, chains, prerouting]
---

# DNAT Chain Location

## Question
In which chain does DNAT (Destination NAT) occur?

## Options
A) INPUT
B) OUTPUT
C) PREROUTING
D) POSTROUTING

## Answer
C

## Explanation
DNAT happens in the PREROUTING chain before the routing decision is made. This is critical because the destination address must be changed before the kernel decides whether to route the packet to a local process (INPUT) or forward it to another network (FORWARD). Port forwarding rules are a common example of DNAT applied in PREROUTING.

## Hook
Why must DNAT happen before the routing decision? What would go wrong if DNAT occurred after routing?
