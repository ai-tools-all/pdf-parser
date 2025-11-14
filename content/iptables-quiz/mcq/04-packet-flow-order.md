---
id: iptables-04-packet-flow-order
day: 2
tags: [iptables, packet-flow, chains, routing]
---

# Packet Flow to Local Process

## Question
What is the correct order of chains for a packet arriving from the network and destined for a local process?

## Options
A) PREROUTING → INPUT → Local Process
B) INPUT → PREROUTING → Local Process
C) PREROUTING → FORWARD → INPUT → Local Process
D) RAW → PREROUTING → FORWARD → Local Process

## Answer
A

## Explanation
When a packet arrives from the network and is destined for a local process, it first goes through PREROUTING (where DNAT can occur), then a routing decision is made. If the routing decision determines the packet is for the local system, it enters the INPUT chain before reaching the local process. The FORWARD chain is only used for packets being routed through the system to another destination.

## Hook
Draw the complete packet flow diagram including the raw and mangle tables. At what point does connection tracking occur?
