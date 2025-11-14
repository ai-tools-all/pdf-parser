---
id: iptables-14-logging
day: 4
tags: [iptables, logging, debugging, troubleshooting]
---

# iptables Logging

## Question
You want to log dropped packets before dropping them. What is the correct approach?

## Options
A) `iptables -A INPUT -j DROP --log-prefix "Dropped: "`
B) `iptables -A INPUT -j LOG --log-prefix "Dropped: " && iptables -A INPUT -j DROP`
C) `iptables -A INPUT -j LOG --log-prefix "Dropped: "` followed by `iptables -A INPUT -j DROP`
D) `iptables -A INPUT -m log --log-prefix "Dropped: " -j DROP`

## Answer
C

## Explanation
Logging requires two separate rules because LOG is a non-terminating target (packets continue to the next rule), while DROP is terminating. You need:
1. First rule: LOG the packet with a prefix for identification
2. Second rule: DROP the packet

Both rules should have the same matching criteria. The packet will be logged and then dropped. Option B tries to combine rules with && which doesn't work in iptables syntax. Option A and D use invalid syntax as DROP doesn't accept --log-prefix and there's no "log" match module with that syntax.

## Hook
Where do iptables LOG messages appear? How can you prevent log flooding from repeated attacks? What's the difference between LOG and ULOG targets?
