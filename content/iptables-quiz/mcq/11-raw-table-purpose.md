---
id: iptables-11-raw-table
day: 4
tags: [iptables, raw, connection-tracking, notrack, performance]
---

# Raw Table and Connection Tracking

## Question
What is the primary purpose of the raw table in iptables?

## Options
A) To filter packets before any other table processes them
B) To bypass connection tracking for specific traffic
C) To perform raw packet inspection without modification
D) To apply rules before packet decryption

## Answer
B

## Explanation
The raw table is primarily used to mark packets that should bypass connection tracking using the NOTRACK target. It processes packets before connection tracking occurs (in PREROUTING and OUTPUT chains only). This is useful for high-volume traffic that doesn't need stateful tracking, as connection tracking has performance overhead. Bypassing conntrack for specific flows can significantly improve performance.

## Hook
What performance benefits does bypassing connection tracking provide? In what scenarios would you use the NOTRACK target?
