---
id: iptables-subj-04-conntrack
level: L4
tags: [iptables, conntrack, connection-tracking, state]
---

# Connection Tracking and Stateful Filtering

## Question
Connection tracking (conntrack) is fundamental to modern Linux firewalls and NAT operation.

**Part 1: Conceptual Understanding**
1. Explain what connection tracking is and why it's necessary
2. Describe the different connection states: NEW, ESTABLISHED, RELATED, INVALID
3. Explain how conntrack enables stateful firewalling

**Part 2: Practical Analysis**
Given these conntrack entries:
```bash
tcp  6 299 ESTABLISHED src=192.168.1.10 dst=8.8.8.8 sport=51234 dport=53 \
     src=8.8.8.8 dst=203.0.113.50 sport=53 dport=12001 [ASSURED]

tcp  6 5 SYN_SENT src=192.168.1.15 dst=93.184.216.34 sport=45678 dport=80 \
     src=93.184.216.34 dst=203.0.113.50 sport=80 dport=45678

udp  17 25 src=192.168.1.20 dst=1.1.1.1 sport=38291 dport=53 \
     src=1.1.1.1 dst=192.168.1.20 sport=53 dport=38291 [ASSURED]
```

Analyze:
1. What NAT is happening in each connection?
2. What does [ASSURED] mean?
3. Why is the second connection not ESTABLISHED?
4. What's different about the third entry (UDP)?

**Part 3: Firewall Rules**
Write iptables rules for a restrictive firewall that:
- Allows internal clients to make outbound connections
- Blocks all unsolicited inbound traffic
- Uses connection tracking for efficiency

## Expected Answer Components

**Mandatory (60%)**
- Definition: Conntrack maintains state table of all connections
- States explained:
  - NEW: First packet of new connection
  - ESTABLISHED: Connection with packets in both directions
  - RELATED: New connection related to existing one (FTP data, ICMP errors)
  - INVALID: Packet doesn't match any known connection
- Stateful firewall allows return traffic without explicit rules
- Analysis showing SNAT is occurring (different source IPs in reply tuple)
- Basic stateful firewall rules:
  ```bash
  iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  iptables -A INPUT -m state --state NEW -i eth1 -j ACCEPT
  iptables -A INPUT -j DROP
  ```

**Bonus (40%)**
- [ASSURED] means bidirectional traffic seen, entry won't be early-evicted
- SYN_SENT means TCP handshake incomplete (only SYN sent, no SYN-ACK yet)
- UDP is connectionless but conntrack still tracks it with timeout
- Conntrack table size limits and tuning
- Performance implications of connection tracking
- How to disable tracking for specific traffic (raw table, NOTRACK)
- Helper modules for complex protocols (nf_conntrack_ftp)

## Common Mistakes
- Confusing connection states with TCP states
- Not understanding the reply tuple in conntrack entries
- Thinking RELATED only applies to same protocol
- Believing UDP doesn't use connection tracking
- Writing redundant rules that conntrack makes unnecessary
- Not considering conntrack table exhaustion in high-traffic scenarios

## Follow-up Questions
1. How does FTP active mode work with connection tracking and firewalls?
2. What happens when the conntrack table fills up?
3. How can you bypass connection tracking for specific high-volume traffic?
4. Explain how conntrack enables NAT to work automatically for related connections.
