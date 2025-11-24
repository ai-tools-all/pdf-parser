---
id: iptables-13-icmp-filtering
day: 4
tags: [iptables, icmp, ping, network-troubleshooting]
---

# ICMP Packet Filtering

## Question
You want to allow incoming ping requests but block all other ICMP messages. Which rule correctly achieves this?

## Options
A) `iptables -A INPUT -p icmp -j ACCEPT`
B) `iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT`
C) `iptables -A INPUT -p icmp --icmp-type 8 -j ACCEPT`
D) Both B and C are correct

## Answer
D

## Explanation
ICMP echo-request (ping) can be specified either by name (echo-request) or by number (type 8). Both formats are valid. After allowing echo-request, you should have a default DROP policy or explicit DROP rule to block other ICMP types. However, blocking all ICMP is generally not recommended as some ICMP messages (like fragmentation-needed, time-exceeded) are essential for proper network operation.

## Hook
Which ICMP message types should you always allow for proper network functionality? What problems arise from blocking all ICMP traffic?
