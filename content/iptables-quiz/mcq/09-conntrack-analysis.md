---
id: iptables-09-conntrack-nat
day: 3
tags: [iptables, conntrack, nat, connection-tracking]
---

# Connection Tracking Analysis

## Question
Consider this conntrack entry:
```
tcp 6 299 ESTABLISHED src=192.168.1.10 dst=142.250.190.46 sport=51100 dport=443 \
    src=142.250.190.46 dst=100.72.5.12 sport=443 dport=30001 [ASSURED]
```
What does this indicate about the connection?

## Options
A) The connection is still in SYN-SENT state
B) NAT is being performed, changing the source port from 51100 to 30001
C) The connection is established and packets have been seen in both directions
D) The connection is about to time out in 6 seconds

## Answer
B

## Explanation
The conntrack entry shows two direction tuples. The first shows the original packet (src=192.168.1.10:51100 → dst=142.250.190.46:443), and the second shows the return path. The return destination is 100.72.5.12:30001, indicating NAT is translating the source address from 192.168.1.10 to 100.72.5.12 and the source port from 51100 to 30001. The [ASSURED] flag means packets have been seen in both directions, making option C also true, but the most significant detail is the NAT operation.

## Hook
What would happen if the conntrack table became full? How does conntrack handle connection timeout for different protocols?
