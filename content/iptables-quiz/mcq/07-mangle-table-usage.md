---
id: iptables-07-mangle-table
day: 2
tags: [iptables, mangle, ttl, tos, packet-modification]
---

# Mangle Table Purpose

## Question
Which table would you use to modify packet TTL (Time To Live) values?

## Options
A) filter
B) nat
C) mangle
D) raw

## Answer
C

## Explanation
The mangle table is used for packet modification, including changing TTL (Time To Live), ToS (Type of Service), and other packet headers. It's available in all chains (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING), making it versatile for various packet manipulation scenarios. Common use cases include TTL modification to prevent traceroute detection or QoS markings.

## Hook
Can you modify the TTL value in the filter table using the TTL target? What are the security implications of modifying TTL values?
