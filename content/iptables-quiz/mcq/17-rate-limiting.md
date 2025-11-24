---
id: iptables-17-rate-limiting
day: 5
tags: [iptables, rate-limiting, ddos, security, limit]
---

# Rate Limiting for DDoS Protection

## Question
Which iptables rule correctly implements rate limiting to accept maximum 10 SSH connection attempts per minute from a single IP?

## Options
A) `iptables -A INPUT -p tcp --dport 22 -m limit --limit 10/minute -j ACCEPT`
B) `iptables -A INPUT -p tcp --dport 22 -m recent --name ssh --set`
   `iptables -A INPUT -p tcp --dport 22 -m recent --name ssh --update --seconds 60 --hitcount 10 -j DROP`
C) `iptables -A INPUT -p tcp --dport 22 -m hashlimit --hashlimit-name ssh --hashlimit-above 10/min --hashlimit-mode srcip -j DROP`
   `iptables -A INPUT -p tcp --dport 22 -j ACCEPT`
D) `iptables -A INPUT -p tcp --dport 22 -m connlimit --connlimit-above 10 -j DROP`

## Answer
C

## Explanation
Option C correctly uses hashlimit to implement per-source-IP rate limiting:
- `hashlimit-mode srcip`: Track rates per source IP address
- `hashlimit-above 10/min`: Trigger when rate exceeds 10 per minute
- DROP packets exceeding the limit, ACCEPT the rest

Option A uses limit (not hashlimit) which applies globally, not per-IP. Option B uses recent which tracks connection attempts but the logic needs refinement. Option D uses connlimit which limits concurrent connections, not connection rate.

## Hook
What's the difference between limit, hashlimit, and recent modules? How would you implement progressive rate limiting (e.g., temporary bans after repeated violations)?
