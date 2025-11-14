# IP Tables and Packet Flow Quiz

A comprehensive quiz on iptables, packet flow, NAT, and Linux firewall concepts organized into MCQ and subjective question formats.

## Structure

```
content/iptables-quiz/
├── mcq/                    # Multiple Choice Questions (10 questions)
│   ├── 01-filter-table-purpose.md
│   ├── 02-dnat-chain.md
│   ├── 03-input-chain-packets.md
│   ├── 04-packet-flow-order.md
│   ├── 05-masquerading-command.md
│   ├── 06-local-output-flow.md
│   ├── 07-mangle-table-usage.md
│   ├── 08-port-forwarding-rules.md
│   ├── 09-conntrack-analysis.md
│   └── 10-complete-forwarding-flow.md
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
- `day`: Learning progression (1-3)
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
- **Connection Tracking**: conntrack, stateful filtering
- **Packet Flow**: Complete traversal through tables and chains
- **Performance**: Optimization, ipset, rule ordering
- **Advanced**: Policy routing, multi-WAN, VoIP, high-performance scenarios

## Usage

### For Students
1. Start with MCQ questions 1-3 (fundamentals)
2. Progress through questions 4-7 (intermediate)
3. Challenge yourself with questions 8-10 (advanced)
4. Attempt subjective questions matching your level
5. Use the "Hook" questions to deepen understanding

### For Instructors
- MCQs suitable for quick assessments
- Subjective questions for assignments/exams
- Progressive difficulty allows customization
- Hooks can be used for classroom discussions
- Common mistakes section helps address misconceptions

## Learning Path

1. **Week 1**: MCQ 1-3, L3 Subjective (Basics)
2. **Week 2**: MCQ 4-7, L4 Subjective (NAT & Forwarding)
3. **Week 3**: MCQ 8-10, L5 Subjective (Advanced Scenarios)

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
