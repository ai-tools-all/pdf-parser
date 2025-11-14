---
id: iptables-19-table-priority
day: 6
tags: [iptables, tables, packet-flow, priority, order]
---

# Table Processing Order

## Question
For a packet in the PREROUTING chain, what is the correct order of table processing?

## Options
A) filter → nat → mangle → raw
B) raw → mangle → nat → filter
C) raw → nat → mangle → filter
D) mangle → nat → raw → filter

## Answer
B

## Explanation
In the PREROUTING chain, tables are processed in this order:
1. **raw**: Connection tracking exemptions (NOTRACK)
2. **mangle**: Packet alterations (TTL, TOS, MARK)
3. **nat**: DNAT and destination modification
4. **filter**: Not available in PREROUTING

The raw table comes first because it must mark packets before connection tracking occurs. Mangle comes before nat so you can mark/modify packets before NAT decisions. The filter table is only available in INPUT, FORWARD, and OUTPUT chains, not PREROUTING or POSTROUTING.

## Hook
Why must the raw table be processed before connection tracking? What would happen if nat came before mangle in the processing order?
