# IP Tables and Packet Flow Quiz

A comprehensive quiz on iptables, packet flow, NAT, and Linux firewall concepts organized into MCQ and subjective question formats.

## Structure

```
content/iptables-quiz/
├── mcq/                    # Multiple Choice Questions (20 questions)
│   ├── 01-filter-table-purpose.md
│   ├── 02-dnat-chain.md
│   ├── 03-input-chain-packets.md
│   ├── 04-packet-flow-order.md
│   ├── 05-masquerading-command.md
│   ├── 06-local-output-flow.md
│   ├── 07-mangle-table-usage.md
│   ├── 08-port-forwarding-rules.md
│   ├── 09-conntrack-analysis.md
│   ├── 10-complete-forwarding-flow.md
│   ├── 11-raw-table-purpose.md
│   ├── 12-docker-iptables.md
│   ├── 13-icmp-filtering.md
│   ├── 14-logging-rules.md
│   ├── 15-default-policy.md
│   ├── 16-ftp-conntrack.md
│   ├── 17-rate-limiting.md
│   ├── 18-source-nat-scenarios.md
│   ├── 19-table-priority-order.md
│   └── 20-ipv6-ip6tables.md
│
└── subjective/             # Open-ended questions
    ├── L3-baseline/        # Beginner level
    │   ├── 01-iptables-basics-and-chains.md
    │   └── 02-nat-basics.md
    ├── L4-baseline/        # Intermediate level
    │   ├── 01-port-forwarding-scenario.md
    │   └── 02-connection-tracking-deep-dive.md
    └── L5-baseline/        # Advanced level
        ├── 01-complex-nat-scenario.md
        └── 02-performance-and-optimization.md
```

## MCQ Format

Each MCQ file includes YAML frontmatter with:
- `id`: Unique question identifier
- `day`: Learning progression (1-6)
- `tags`: Topic categorization

Question structure:
- **Question**: The problem statement
- **Options**: Four choices (A-D)
- **Answer**: Correct option
- **Explanation**: Detailed reasoning
- **Hook**: Follow-up question for deeper understanding

## Difficulty Levels

### Level 1 (Questions 1-3): Fundamentals
- Basic iptables tables and chains
- Simple packet flow concepts
- Core terminology

### Level 2 (Questions 4-7): Intermediate
- Packet flow through multiple chains
- NAT configuration commands
- Connection states
- Table usage

### Level 3 (Questions 8-10): Advanced
- Complex port forwarding scenarios
- Connection tracking analysis
- Complete packet flow with multiple tables
- NAT troubleshooting

### Level 4 (Questions 11-15): Specialized Topics
- Raw table and connection tracking bypass
- Docker integration with iptables
- ICMP filtering and network troubleshooting
- Logging and debugging techniques
- Security policies and best practices

### Level 5 (Questions 16-20): Expert Topics
- FTP and connection tracking helpers
- Rate limiting and DDoS protection
- SNAT vs MASQUERADE scenarios
- Table processing priority and order
- IPv6 and dual-stack firewall configuration

## Subjective Questions

### L3-baseline (Beginner)
Focus on fundamental concepts with guided scenarios:
- Basic chain traversal for local processes
- Simple NAT configurations (masquerading)
- Understanding packet flow diagrams

### L4-baseline (Intermediate)
Real-world scenarios requiring deeper knowledge:
- Multi-service port forwarding setups
- Connection tracking mechanics
- Stateful firewall design
- Troubleshooting methodologies

### L5-baseline (Advanced)
Complex production scenarios:
- Multi-WAN policy routing with NAT
- Performance optimization at scale
- Advanced protocols (VoIP/SIP with NAT)
- High-traffic environments (100k+ PPS)
- Migration strategies (nftables, eBPF/XDP)

## Topics Covered

- **Tables**: filter, nat, mangle, raw
- **Chains**: PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING
- **NAT**: SNAT, DNAT, Masquerading, Port Forwarding
- **Connection Tracking**: conntrack, stateful filtering, helpers (FTP)
- **Packet Flow**: Complete traversal through tables and chains, processing order
- **Performance**: Optimization, ipset, rule ordering, NOTRACK
- **Security**: Default policies, rate limiting, DDoS protection, logging
- **Container Networking**: Docker iptables integration
- **Protocol-Specific**: ICMP filtering, FTP handling, VoIP/SIP
- **Advanced**: Policy routing, multi-WAN, VoIP, high-performance scenarios, IPv6/ip6tables

## Usage

### For Students
1. Start with MCQ questions 1-3 (fundamentals)
2. Progress through questions 4-7 (intermediate)
3. Challenge yourself with questions 8-10 (advanced)
4. Explore specialized topics in questions 11-15
5. Master expert topics in questions 16-20
6. Attempt subjective questions matching your level
7. Use the "Hook" questions to deepen understanding

### For Instructors
- MCQs suitable for quick assessments
- Subjective questions for assignments/exams
- Progressive difficulty allows customization
- Hooks can be used for classroom discussions
- Common mistakes section helps address misconceptions

## Learning Path

### 3-Week Course
1. **Week 1**: MCQ 1-3, L3 Subjective (Basics)
2. **Week 2**: MCQ 4-7, L4 Subjective (NAT & Forwarding)
3. **Week 3**: MCQ 8-10, L5 Subjective (Advanced Scenarios)

### 6-Week Course (Extended)
1. **Week 1**: MCQ 1-3 (Fundamentals)
2. **Week 2**: MCQ 4-7 (Intermediate), L3 Subjective
3. **Week 3**: MCQ 8-10 (Advanced NAT & Flow)
4. **Week 4**: MCQ 11-15 (Specialized Topics), L4 Subjective
5. **Week 5**: MCQ 16-20 (Expert Topics)
6. **Week 6**: L5 Subjective (Complex Production Scenarios)

## Assessment Rubrics

Subjective questions include:
- **Mandatory components** (60-70%): Core concepts that must be demonstrated
- **Bonus components** (30-40%): Advanced knowledge and optimizations
- **Common mistakes**: What to watch for when grading
- **Follow-up questions**: For oral exams or deeper exploration

## References

- Based on Linux iptables/netfilter documentation
- Follows standard networking fundamentals
- Aligned with enterprise firewall configurations
- Includes modern alternatives (nftables, eBPF)
