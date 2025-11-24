---
id: iptables-subj-02-nat-basics
level: L3
tags: [iptables, nat, masquerading, snat, dnat]
---

# Network Address Translation Fundamentals

## Question
A small office has a private network 192.168.1.0/24 with multiple computers that need to access the internet through a Linux router with two interfaces:
- eth0: Connected to ISP with public IP 203.0.113.50
- eth1: Connected to local network with IP 192.168.1.1

Explain how NAT works in this scenario:

1. What type of NAT is needed? (SNAT/DNAT/Masquerading)
2. In which chain and table does this NAT occur?
3. Write the iptables command to enable this
4. Trace what happens to a packet from 192.168.1.10 going to 8.8.8.8:53 (DNS)
   - Show the packet headers before and after NAT
   - Explain how the return packet finds its way back

## Expected Answer Components

**Mandatory (60%)**
- Type: MASQUERADE (or SNAT) - source NAT needed
- Chain/Table: POSTROUTING in nat table
- Command: `iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE`
- Outgoing packet transformation:
  - Before: src=192.168.1.10:random dst=8.8.8.8:53
  - After: src=203.0.113.50:translated_port dst=8.8.8.8:53
- Return tracking via conntrack table

**Bonus (40%)**
- Difference between MASQUERADE and SNAT (`--to-source 203.0.113.50`)
- Connection tracking details (how kernel maintains NAT mapping)
- Port range exhaustion considerations
- IP forwarding requirement: `echo 1 > /proc/sys/net/ipv4/ip_forward`
- Mention of PAT (Port Address Translation) vs NAT

## Common Mistakes
- Putting NAT rule in PREROUTING instead of POSTROUTING
- Using DNAT instead of SNAT/MASQUERADE
- Forgetting to enable IP forwarding
- Not understanding that masquerading automatically handles dynamic IPs
- Confusing which interface to specify (-o vs -i)

## Follow-up Questions
1. What happens if two internal hosts use the same source port connecting to the same destination?
2. How would you configure port forwarding from the public IP to an internal server?
3. When would you use SNAT instead of MASQUERADE?
