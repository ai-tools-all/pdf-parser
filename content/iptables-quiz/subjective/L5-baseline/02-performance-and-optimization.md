---
id: iptables-subj-06-performance
level: L5
tags: [iptables, performance, optimization, ipset, nftables]
---

# iptables Performance Optimization and Advanced Techniques

## Question
You're operating a high-traffic web hosting environment processing 100,000+ packets per second. The current iptables ruleset has performance issues:

**Current Setup (Problematic):**
```bash
# 500+ rules like this:
iptables -A INPUT -s 1.2.3.4 -j DROP
iptables -A INPUT -s 1.2.3.5 -j DROP
... (500 more IPs)

# Service rules
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rate limiting per-IP (also slow)
iptables -A INPUT -p tcp --dport 80 -m recent --name http --rcheck --seconds 60 --hitcount 100 -j DROP
```

**Symptoms:**
- High CPU usage in kernel (softirq)
- Dropped packets under load
- Slow rule evaluation

**Tasks:**
1. Identify performance bottlenecks in the current configuration
2. Optimize using ipset
3. Optimize rule ordering and structure
4. Implement connection tracking optimizations
5. Discuss alternatives (nftables, eBPF/XDP)
6. Provide monitoring and debugging strategies

## Expected Answer Components

**Mandatory (60%)**
- Problems identified:
  - Linear rule traversal for 500+ DROP rules (O(n) complexity)
  - Each packet checks all rules before matching
  - Recent module maintains per-IP state inefficiently
  - No rule organization/chaining

- ipset optimization:
  ```bash
  ipset create blacklist hash:ip hashsize 4096
  ipset add blacklist 1.2.3.4
  ipset add blacklist 1.2.3.5
  # ... add all IPs
  iptables -A INPUT -m set --match-set blacklist src -j DROP
  ```

- Rule ordering (most specific/common first):
  ```bash
  iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  iptables -A INPUT -i lo -j ACCEPT
  iptables -A INPUT -m set --match-set blacklist src -j DROP
  iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT
  iptables -A INPUT -j DROP
  ```

- Connection tracking optimization:
  ```bash
  # Disable tracking for high-volume traffic that doesn't need it
  iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
  iptables -t raw -A OUTPUT -p tcp --sport 80 -j NOTRACK
  ```

**Bonus (40%)**
- Custom chains for organization:
  ```bash
  iptables -N SECURITY_CHECKS
  iptables -A INPUT -j SECURITY_CHECKS
  iptables -A SECURITY_CHECKS -m set --match-set blacklist src -j DROP
  ```

- Conntrack table tuning:
  ```bash
  sysctl -w net.netfilter.nf_conntrack_max=1000000
  sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600
  sysctl -w net.netfilter.nf_conntrack_buckets=250000
  ```

- Hashlimit instead of recent for better performance:
  ```bash
  iptables -A INPUT -p tcp --dport 80 -m hashlimit \
    --hashlimit-name http --hashlimit-above 100/sec \
    --hashlimit-burst 200 --hashlimit-mode srcip -j DROP
  ```

- Migration to nftables benefits:
  - Better performance (O(1) lookups with sets/maps)
  - Atomic rule updates
  - Better syntax and scripting
  - Native set/map support

- eBPF/XDP for even higher performance:
  - Packet filtering at driver level
  - Before packet enters kernel network stack
  - Can handle millions of PPS

- Performance monitoring:
  ```bash
  iptables -L -n -v --line-numbers  # Check packet/byte counters
  perf top -e cycles:k  # Kernel CPU usage
  conntrack -C  # Connection count
  cat /proc/net/ip_conntrack | wc -l
  ```

## Common Mistakes
- Adding ACCEPT rules at the end instead of beginning
- Not using ipset for large IP lists
- Over-using complex matches (regex, string matching)
- Not disabling conntrack for high-volume stateless traffic
- Inefficient rate limiting with recent module
- Not organizing rules into custom chains
- Missing optimization opportunities in rule ordering
- Not monitoring per-rule hit counts to optimize ordering

## Follow-up Questions
1. When should you disable connection tracking, and what are the trade-offs?
2. How does nftables improve upon iptables architecture?
3. What role does receive packet steering (RPS/RFS) play in firewall performance?
4. How would you benchmark and compare different iptables configurations?
5. At what point should you consider moving to XDP/eBPF instead of iptables?
6. Explain the performance difference between hash:ip and hash:net in ipset
7. How do you safely deploy rule changes in production without downtime?
8. What metrics should you monitor for a production firewall?
