---
id: iptables-18-snat-scenarios
day: 5
tags: [iptables, snat, nat, source-nat, networking]
---

# SNAT vs MASQUERADE

## Question
What is the key difference between SNAT and MASQUERADE in iptables?

## Options
A) SNAT works for IPv4, MASQUERADE works for IPv6
B) SNAT requires specifying a fixed source IP, MASQUERADE uses the outgoing interface's current IP
C) SNAT is faster but MASQUERADE is more secure
D) SNAT works in PREROUTING, MASQUERADE works in POSTROUTING

## Answer
B

## Explanation
The key difference is:
- **SNAT**: Requires explicitly specifying the source IP with `--to-source`, e.g., `iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.50`
- **MASQUERADE**: Automatically uses the current IP address of the outgoing interface

MASQUERADE is useful for dynamic IP addresses (DHCP, PPPoE) but has slightly more overhead as it must look up the interface IP for each packet. SNAT is more efficient for static IPs. Both work in POSTROUTING only.

## Hook
In what scenarios would MASQUERADE fail to work properly? What happens when you use SNAT with an IP address that changes?
