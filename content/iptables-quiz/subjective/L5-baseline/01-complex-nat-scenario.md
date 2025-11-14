---
id: iptables-subj-05-complex-nat
level: L5
tags: [iptables, nat, dnat, snat, multi-wan, policy-routing]
---

# Complex NAT and Multi-WAN Scenario

## Question
You're architecting a complex network with multiple internet connections and advanced NAT requirements:

```
ISP1 (eth0: 203.0.113.50/30, gateway: 203.0.113.49)
ISP2 (eth1: 198.51.100.10/30, gateway: 198.51.100.9)
         ↓
   [Linux Router]
         ↓
Internal Network (eth2: 10.0.0.1/24)
   ├─ Department A: 10.0.0.0/25 → Must use ISP1
   ├─ Department B: 10.0.0.128/25 → Must use ISP2
   ├─ Public Web Server: 10.0.0.10
   │    - Accessible via both 203.0.113.50:80 and 198.51.100.10:80
   └─ VoIP Server: 10.0.0.20
        - External IP: 203.0.113.50:5060
        - Needs both UDP and TCP
```

**Requirements:**
1. Implement policy-based routing so each department uses their assigned ISP
2. Port forward both public IPs to the web server
3. Handle VoIP server with proper NAT for signaling and RTP
4. Ensure return traffic goes back through the correct interface
5. Handle asymmetric routing scenarios

**Deliverables:**
1. Complete iptables ruleset with explanations
2. Policy routing rules (ip rule / ip route)
3. Packet flow diagrams for:
   - Dept A client → Internet
   - External client → Web server via ISP1
   - External client → VoIP server (SIP signaling + RTP media)
4. Troubleshooting strategy for common issues

## Expected Answer Components

**Mandatory (60%)**
- Policy routing setup:
  ```bash
  ip rule add from 10.0.0.0/25 table 100
  ip rule add from 10.0.0.128/25 table 200
  ip route add default via 203.0.113.49 table 100
  ip route add default via 198.51.100.9 table 200
  ```
- Department-specific SNAT:
  ```bash
  iptables -t nat -A POSTROUTING -s 10.0.0.0/25 -o eth0 -j SNAT --to-source 203.0.113.50
  iptables -t nat -A POSTROUTING -s 10.0.0.128/25 -o eth1 -j SNAT --to-source 198.51.100.10
  ```
- Dual DNAT for web server:
  ```bash
  iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 10.0.0.10:80
  iptables -t nat -A PREROUTING -i eth1 -p tcp --dport 80 -j DNAT --to-destination 10.0.0.10:80
  ```
- VoIP DNAT for both TCP and UDP:
  ```bash
  iptables -t nat -A PREROUTING -i eth0 -p udp --dport 5060 -j DNAT --to-destination 10.0.0.20:5060
  iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 5060 -j DNAT --to-destination 10.0.0.20:5060
  iptables -t nat -A PREROUTING -i eth0 -p udp --dport 10000:20000 -j DNAT --to-destination 10.0.0.20
  ```
- FORWARD rules for all services

**Bonus (40%)**
- Handling asymmetric routing with conntrack zones or route marking
- SIP ALG considerations (nf_conntrack_sip)
- Source NAT for servers' outbound traffic to match incoming interface
- Failover mechanisms if one ISP goes down
- Connection marking for policy routing:
  ```bash
  iptables -t mangle -A PREROUTING -i eth2 -s 10.0.0.0/25 -j MARK --set-mark 100
  ip rule add fwmark 100 table 100
  ```
- RPF (Reverse Path Filtering) configuration
- Load balancing considerations between ISPs
- Netfilter optimization for high-performance scenarios

## Common Mistakes
- Forgetting that POSTROUTING SNAT must match the outgoing interface
- Not handling return traffic routing (servers sending replies via correct interface)
- Overlooking VoIP's RELATED connections for RTP streams
- Incorrect policy routing leading to routing loops
- Not considering MTU issues with multiple WANs
- Asymmetric routing breaking stateful connection tracking
- Wrong source NAT for server-originated traffic
- Not handling ICMP properly in policy routing

## Follow-up Questions
1. How do you handle the scenario where the web server initiates an outbound connection? Which ISP does it use?
2. What happens if ISP1 fails? How can you implement automatic failover?
3. Explain how to debug asymmetric routing issues with conntrack
4. How would you implement load balancing across both ISPs?
5. What security implications arise from having services accessible via multiple public IPs?
6. How does SIP ALG affect NAT traversal for VoIP, and when should you disable it?
