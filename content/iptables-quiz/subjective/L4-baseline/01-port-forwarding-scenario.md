---
id: iptables-subj-03-port-forwarding
level: L4
tags: [iptables, dnat, port-forwarding, forward-chain]
---

# Port Forwarding and DNAT Configuration

## Question
You are setting up a Linux firewall/router for a company network. The network topology is:

```
Internet (eth0: 203.0.113.50)
    ↓
[Linux Firewall]
    ↓
Internal Network (eth1: 192.168.1.1/24)
    ├─ Web Server: 192.168.1.20
    └─ Mail Server: 192.168.1.30
```

Requirements:
1. External clients should access the web server using 203.0.113.50:80
2. External clients should access the mail server using 203.0.113.50:25
3. Internal clients can access the internet
4. Default policy is DROP for FORWARD chain

Provide:
1. All necessary iptables rules for this setup
2. Explanation of why each rule is needed
3. Complete packet flow diagram for: External client (1.2.3.4) → Web Server (192.168.1.20:80)
4. Troubleshooting steps if port forwarding doesn't work

## Expected Answer Components

**Mandatory (70%)**
- DNAT rules in PREROUTING:
  ```bash
  iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.1.20:80
  iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 25 -j DNAT --to-destination 192.168.1.30:25
  ```
- FORWARD chain rules:
  ```bash
  iptables -A FORWARD -p tcp -d 192.168.1.20 --dport 80 -j ACCEPT
  iptables -A FORWARD -p tcp -d 192.168.1.30 --dport 25 -j ACCEPT
  iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
  ```
- Masquerading for internal clients:
  ```bash
  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
  iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
  ```
- Packet flow showing PREROUTING DNAT → Routing → FORWARD → POSTROUTING

**Bonus (30%)**
- Enable IP forwarding: `sysctl -w net.ipv4.ip_forward=1`
- FORWARD rule for return traffic from internal servers
- Logging rules for debugging
- Security hardening (rate limiting, source IP restrictions)
- Discussion of hairpin NAT for internal clients accessing servers via public IP

## Common Mistakes
- Only adding DNAT rule without FORWARD rule
- Using INPUT chain instead of FORWARD chain
- Wrong interface specification (-i vs -o)
- Forgetting ESTABLISHED,RELATED rule for return traffic
- Not enabling IP forwarding at OS level
- Incorrect order of rule evaluation

## Follow-up Questions
1. Why do you need both DNAT and FORWARD rules?
2. What happens if an internal client (192.168.1.50) tries to access 203.0.113.50:80?
3. How would you troubleshoot if external clients can't reach the web server?
4. What changes would you make to forward port 8080 externally to port 80 internally?
