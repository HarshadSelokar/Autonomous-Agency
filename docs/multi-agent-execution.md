# Multi-Agent Execution & Coordination Operational Guide (Phase 22)

## Architectural Target Flow

```
                    COMPANY OS
                         |
                         v
                    OBJECTIVE
                         |
                         v
                       PLAN
                         |
                         v
                       TASK
                         |
                         v
                  SWARM PLANNER
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          AGENT A     AGENT B     AGENT C
             |           |           |
             v           v           v
          SUBTASK      SUBTASK      SUBTASK
             |           |           |
             +-----------+-----------+
                         |
                         v
                    COORDINATION
                         |
                         v
                     AGGREGATION
                         |
                         v
                      EVIDENCE
                         |
                         v
                    VERIFICATION
                         |
                  +------+------+
                  |             |
                  v             v
              VERIFIED       FAILED
                  |             |
                  v             v
               COMPLETE      RECOVERY
```

---

## Distributed Execution Topology

```
                       COMPANY OS
                           |
                           v
                      TASK ENGINE
                           |
                           v
                    SWARM COORDINATOR
                           |
                 +---------+---------+
                 |         |         |
                 v         v         v
              Worker    Worker    Worker
                 |         |         |
                 v         v         v
              Agent     Agent     Agent
                 |         |         |
                 +---------+---------+
                           |
                           v
                      TOOL SYSTEM
                           |
                           v
                       EVIDENCE
                           |
                           v
                     VERIFICATION
                           |
                           v
                       RECOVERY
```

---

## Operating Guidelines & Security Protection
1. **No Autonomous Organizational Authority**: Swarms cannot modify company hierarchy, fire employees, alter governance policies, or grant themselves elevated privileges.
2. **No Unbounded Fan-out**: Nested swarm creation is strictly capped at `max_swarm_depth` $\le 2$.
3. **Prompt Injection Protection**: All inter-agent messages are treated strictly as data and sanitized against policy bypass attempts.
4. **Cross-Swarm Isolation**: Workspaces, context, and messages are isolated per swarm.
