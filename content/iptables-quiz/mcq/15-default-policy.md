---
id: iptables-15-default-policy
day: 5
tags: [iptables, security, policy, best-practices]
---

# Default Policy Configuration

## Question
From a security perspective, which default policy configuration is considered best practice for a server firewall?

## Options
A) INPUT: ACCEPT, FORWARD: ACCEPT, OUTPUT: ACCEPT (allow everything)
B) INPUT: DROP, FORWARD: DROP, OUTPUT: ACCEPT (restrictive inbound)
C) INPUT: DROP, FORWARD: DROP, OUTPUT: DROP (deny everything)
D) INPUT: ACCEPT, FORWARD: DROP, OUTPUT: ACCEPT (allow local traffic)

## Answer
B

## Explanation
Best practice for a server firewall is INPUT: DROP, FORWARD: DROP, OUTPUT: ACCEPT. This means:
- INPUT DROP: Block all incoming traffic by default, only allow explicitly permitted services
- FORWARD DROP: Don't route traffic by default (only relevant if IP forwarding is enabled)
- OUTPUT ACCEPT: Allow outbound connections (can be more restrictive for high-security environments)

This follows the "default deny" security principle. You then add explicit ACCEPT rules for required services. Option C is too restrictive for most servers as it blocks legitimate outbound traffic.

## Hook
In what scenarios would you set OUTPUT policy to DROP? What additional considerations are needed when changing default policies on a production system?
