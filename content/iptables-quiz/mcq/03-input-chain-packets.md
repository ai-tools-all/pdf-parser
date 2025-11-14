---
id: iptables-03-input-chain
day: 1
tags: [iptables, chains, input, local-process]
---

# INPUT Chain Function

## Question
Which built-in chain processes packets destined for local processes?

## Options
A) FORWARD
B) INPUT
C) OUTPUT
D) PREROUTING

## Answer
B

## Explanation
The INPUT chain processes packets that are destined for local processes on the system. After the routing decision determines the packet is for the local machine (not to be forwarded), it goes through the INPUT chain where firewall rules can accept or drop the packet before it reaches the application.

## Hook
What is the relationship between the INPUT and OUTPUT chains? Can a packet traverse both chains in a single flow?
