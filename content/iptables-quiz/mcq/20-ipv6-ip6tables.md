---
id: iptables-20-ipv6
day: 6
tags: [ip6tables, ipv6, firewall, dual-stack]
---

# IPv6 and ip6tables

## Question
On a dual-stack system running both IPv4 and IPv6, you configure iptables rules to block all incoming traffic except SSH. What additional step is required for complete protection?

## Options
A) Nothing, iptables rules automatically apply to both IPv4 and IPv6
B) Enable the IPv6 module in iptables with `modprobe ip6_tables`
C) Configure equivalent ip6tables rules for IPv6 traffic
D) Disable IPv6 entirely with `sysctl -w net.ipv6.conf.all.disable_ipv6=1`

## Answer
C

## Explanation
iptables and ip6tables are completely separate systems:
- **iptables**: Manages IPv4 traffic only
- **ip6tables**: Manages IPv6 traffic separately

You must configure both firewalls independently. If you only configure iptables, IPv6 traffic will bypass your firewall rules entirely, creating a security vulnerability. On dual-stack systems, always configure both:
```bash
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 22 -j ACCEPT
```

Modern systems can use nftables which handles both IPv4 and IPv6 in a unified framework.

## Hook
What are the security implications of running IPv6 without firewall rules on a dual-stack system? How does nftables simplify dual-stack firewall management?
