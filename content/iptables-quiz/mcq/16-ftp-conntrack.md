---
id: iptables-16-ftp-conntrack
day: 5
tags: [iptables, ftp, conntrack, helpers, related]
---

# FTP and Connection Tracking Helpers

## Question
FTP active mode uses a control connection (port 21) and a separate data connection initiated by the server. How does iptables handle the data connection with a stateful firewall?

## Options
A) The data connection is tracked as NEW and must be explicitly allowed
B) The FTP connection tracking helper marks the data connection as RELATED
C) FTP doesn't work with stateful firewalls due to dynamic ports
D) The data connection uses the same conntrack entry as the control connection

## Answer
B

## Explanation
The nf_conntrack_ftp module (connection tracking helper) inspects FTP control channel traffic to identify upcoming data connections. When the FTP server initiates a data connection back to the client, conntrack marks it as RELATED to the original control connection. This allows rules like `iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT` to automatically allow the data connection without knowing the specific port in advance.

## Hook
What's the difference between FTP active and passive modes in terms of firewall traversal? Why might you want to disable FTP connection tracking helpers in some environments?
