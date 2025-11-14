---
id: iptables-12-docker-iptables
day: 4
tags: [iptables, docker, nat, container-networking]
---

# Docker and iptables Integration

## Question
When Docker publishes a container port with `-p 8080:80`, which iptables operations does Docker automatically configure?

## Options
A) Only a DNAT rule in PREROUTING to forward traffic to the container
B) A DNAT rule in a custom DOCKER chain and corresponding FORWARD rules
C) Only SNAT rules in POSTROUTING for container outbound traffic
D) Filter rules in INPUT chain to allow traffic to the container

## Answer
B

## Explanation
Docker creates custom chains (DOCKER, DOCKER-ISOLATION, etc.) and inserts rules into them. For port publishing, Docker adds:
1. A DNAT rule in the DOCKER chain (called from PREROUTING) to translate the destination to the container's IP and port
2. ACCEPT rules in the DOCKER chain (called from FORWARD) to allow the traffic
3. Masquerading rules for container-to-external traffic

Docker manages these rules automatically and removes them when containers are stopped.

## Hook
What happens to Docker's iptables rules if you manually flush all iptables rules? How does Docker's iptables integration affect custom firewall rules?
