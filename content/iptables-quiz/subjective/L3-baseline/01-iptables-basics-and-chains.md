---
id: iptables-subj-01-basics
level: L3
tags: [iptables, basics, chains, packet-flow]
---

# iptables Basics and Chain Traversal

## Question
Explain the basic workflow of how a packet traverses iptables chains when it arrives from an external network destined for a local web server running on port 80. Include in your answer:

1. The order of chains the packet traverses
2. Which table(s) are involved at each step
3. What happens at the routing decision point
4. How you would write a rule to allow this traffic

Then, provide a concrete example showing what happens when:
- Client 203.0.113.5 sends a packet to your server's IP 192.0.2.10:80
- Your server has a default DROP policy on the INPUT chain

## Expected Answer Components

**Mandatory (60%)**
- Correct chain order: PREROUTING → (routing decision) → INPUT → Local Process
- Tables involved: raw, mangle, nat in PREROUTING; filter in INPUT
- Routing decision determines packet is for local system
- Basic rule: `iptables -A INPUT -p tcp --dport 80 -j ACCEPT`

**Bonus (40%)**
- State tracking: `iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT`
- Mention of connection tracking in raw table
- Security considerations (limiting source IPs, rate limiting)
- Explanation of why PREROUTING doesn't apply filtering for incoming local traffic

## Common Mistakes
- Confusing PREROUTING with INPUT for local traffic filtering
- Forgetting the routing decision step
- Not understanding that filter table is separate from nat table
- Thinking packets touch FORWARD chain when destined for local processes

## Follow-up Questions
1. How would the packet flow differ if the web server was on a different machine (192.168.1.20) behind this firewall?
2. What additional rules would you need for the server to respond to clients?
3. How does connection tracking simplify rule management?
