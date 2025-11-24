---
id: iptables-05-masquerading
day: 2
tags: [iptables, nat, masquerading, snat, postrouting]
---

# Masquerading Configuration

## Question
Which iptables command enables masquerading for outgoing traffic on interface eth0?

## Options
A) `iptables -t filter -A OUTPUT -o eth0 -j MASQUERADE`
B) `iptables -t nat -A PREROUTING -i eth0 -j MASQUERADE`
C) `iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE`
D) `iptables -t mangle -A POSTROUTING -o eth0 -j MASQUERADE`

## Answer
C

## Explanation
Masquerading (a form of SNAT - Source NAT) happens in the POSTROUTING chain of the nat table, after the routing decision has been made. The `-o eth0` specifies the outgoing interface. Masquerading is particularly useful for dynamic IP addresses as it automatically uses the current IP of the outgoing interface, unlike SNAT which requires specifying a fixed source IP.

## Hook
What is the difference between MASQUERADE and SNAT? When would you choose one over the other?
