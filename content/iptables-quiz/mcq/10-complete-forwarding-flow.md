---
id: iptables-10-complete-flow
day: 3
tags: [iptables, packet-flow, forwarding, tables, chains]
---

# Complete Forwarding Packet Flow

## Question
A packet arrives on eth0 from 10.0.0.5:5000 destined for 192.168.1.100:80. The system has IP forwarding enabled and routes the packet to eth1. Through which tables and chains does this packet traverse IN ORDER?

## Options
A) raw(PREROUTING) → nat(PREROUTING) → filter(FORWARD) → nat(POSTROUTING)
B) raw(INPUT) → filter(INPUT) → filter(OUTPUT) → nat(POSTROUTING)
C) raw(PREROUTING) → nat(PREROUTING) → filter(INPUT) → filter(OUTPUT)
D) nat(PREROUTING) → filter(INPUT) → filter(FORWARD) → mangle(POSTROUTING)

## Answer
A

## Explanation
For a forwarded packet, the complete flow is:
1. **raw(PREROUTING)**: First table for connection tracking exemptions
2. **mangle(PREROUTING)**: Packet modification (not listed in option)
3. **nat(PREROUTING)**: DNAT happens here if needed
4. **Routing decision**: Determines packet needs forwarding
5. **mangle(FORWARD)**: Additional packet modification
6. **filter(FORWARD)**: Firewall filtering for forwarded packets
7. **mangle(POSTROUTING)**: More packet modification
8. **nat(POSTROUTING)**: SNAT/Masquerading happens here

Option A is the most accurate, though simplified. The packet never touches INPUT or OUTPUT chains since it's being forwarded, not processed locally.

## Hook
If you wanted to implement a router with NAT and firewall capabilities, which minimum set of rules would you need in which tables?
