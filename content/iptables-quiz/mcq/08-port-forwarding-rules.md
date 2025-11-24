---
id: iptables-08-port-forwarding
day: 3
tags: [iptables, nat, dnat, forward, port-forwarding]
---

# Port Forwarding Requirements

## Question
You want to forward external port 8080 to internal server 192.168.1.20:80. Which two rules are required?

## Options
A) DNAT in PREROUTING and ACCEPT in INPUT
B) DNAT in POSTROUTING and ACCEPT in FORWARD
C) DNAT in PREROUTING and ACCEPT in FORWARD
D) SNAT in PREROUTING and ACCEPT in OUTPUT

## Answer
C

## Explanation
Port forwarding requires two rules:
1. A DNAT rule in the PREROUTING chain to change the destination: `iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.20:80`
2. An ACCEPT rule in the FORWARD chain to allow the forwarded packets: `iptables -A FORWARD -p tcp -d 192.168.1.20 --dport 80 -j ACCEPT`

The packet is being routed to a different host, so it goes through FORWARD, not INPUT (which is only for local processes).

## Hook
Do you need a SNAT/MASQUERADE rule for port forwarding to work? Under what circumstances would return traffic fail without it?
