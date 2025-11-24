---
id: iptables-01-filter-table
day: 1
tags: [iptables, tables, filtering, basics]
---

# Filter Table Purpose

## Question
Which iptables table is primarily used for packet filtering (allow/deny)?

## Options
A) nat
B) mangle
C) filter
D) raw

## Answer
C

## Explanation
The filter table is the default table used for packet filtering operations. It contains the INPUT, FORWARD, and OUTPUT chains and is used to make decisions about whether packets should be allowed or denied. This is the most commonly used table for firewall rules.

## Hook
What happens to a packet when it matches a DROP rule in the filter table? Does it get logged automatically?
