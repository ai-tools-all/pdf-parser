# IP Tables and Packet Flow Quiz - Answer Key

## Quick Reference

### Level 1: Fundamentals (Easy)
1. **C** - filter table
2. **C** - PREROUTING chain
3. **B** - INPUT chain

### Level 2: Intermediate
4. **A** - PREROUTING → INPUT → Local Process
5. **C** - `iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE`
6. **A** - OUTPUT → POSTROUTING
7. **C** - mangle table

### Level 3: Advanced
8. **C** - DNAT in PREROUTING and ACCEPT in FORWARD
9. **B** - NAT is being performed (though C is also technically correct)
10. **A** - raw(PREROUTING) → nat(PREROUTING) → filter(FORWARD) → nat(POSTROUTING)

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 0-3 | Beginner | Review basic iptables concepts, tables, and chains |
| 4-6 | Intermediate | Good foundation - practice packet flow scenarios |
| 7-8 | Advanced | Strong understanding - focus on complex NAT scenarios |
| 9-10 | Expert | Excellent mastery of iptables and packet flow |
