# Multi-Agent Swarms & Distributed Agent Coordination (Phase 22)

## Architectural Principle
> **"A SWARM IS AN EXECUTION TOPOLOGY, NOT A NEW ORGANIZATION."**

Phase 22 introduces a Multi-Agent Swarm execution layer above the Company Operating System. Swarms are temporary, governed execution structures containing multiple specialized agents coordinating safely to solve complex parent tasks.

---

## Core Invariants & Boundaries
- **Subordination**: Swarms remain strictly subordinate to the Company OS, Task Engine, Governance System, Model Router, Tool Pipeline, Verification Engine, and Recovery Engine.
- **No Independent Task System**: Every swarm subtask is tied to an authoritative `Task` from the Task Engine.
- **Strict Invariants**:
  - `EMPLOYEE != AGENT != LLM`
  - `MANAGER ⊆ EMPLOYEE`
  - `TASK != SWARM != TEAM != DEPARTMENT != ORGANIZATION`
  - `CLAIM != EVIDENCE != VERIFICATION != COMPLETION`

---

## Swarm Entities & Lifecycle States

### Swarm Aggregate Root (`Swarm`)
- **`id`**: Unique swarm identifier (`sw_*`).
- **`code`**: Human-readable code (`SWARM-XXXXXX`).
- **`parent_task_id`**: Authoritative parent task reference.
- **`coordination_mode`**: `PARALLEL`, `SEQUENTIAL`, `PIPELINE`, `SPECIALIST`, `DEBATE`, `CONSENSUS`, `REVIEW`, `MAP_REDUCE`, `HIERARCHICAL`.
- **`status`**: `CREATED` $\rightarrow$ `PLANNING` $\rightarrow$ `FORMING` $\rightarrow$ `READY` $\rightarrow$ `RUNNING` $\rightarrow$ `PAUSED` $\rightarrow$ `DEGRADED` $\rightarrow$ `COMPLETING` $\rightarrow$ `VERIFYING` $\rightarrow$ `COMPLETED` (Failure states: `FAILED`, `CANCELLED`, `ESCALATED`).
- **`depth`**: Nesting depth ($\le 2$).

### Resource Budget (`SwarmBudget`)
Enforces hard resource ceilings across 6 dimensions:
- `max_execution_time_seconds` (default: 3600s)
- `max_model_cost` (default: $50.00)
- `max_tool_calls` (default: 200)
- `max_tokens` (default: 500,000)
- `max_retries` (default: 5)
- `max_swarm_depth` (default: 2)

---

## Coordination Topologies
1. **`SPECIALIST`**: Role-based capability matching (Research Agent, Architect Agent, Backend Agent, QA Agent, Security Agent, Reviewer Agent, Coordinator).
2. **`PARALLEL`**: Simultaneous execution of independent subtasks up to concurrency limits.
3. **`PIPELINE`**: Sequential handoff where Stage $i+1$ consumes verified output from Stage $i$.
4. **`MAP_REDUCE`**: Parallel map workers execute subtasks followed by a synthesis reducer.
5. **`DEBATE` / `CONSENSUS`**: Proposal $\rightarrow$ Critique $\rightarrow$ Synthesis flow.

---

## Result Aggregation, Disagreements & Verification
- **Aggregation**: Combines member outputs via deterministic merge, coordinator synthesis, or evidence-weighted aggregation.
- **Conflict Resolution**: Inter-agent disagreements (`result_a`, `result_b`) generate structured `SwarmConflict` records and trigger independent evidence verification.
- **Independent Verification**: Swarm completion requires verification from Phase 10 `VerificationEngine`. `CLAIM != EVIDENCE != VERIFICATION != COMPLETION`.

---

## REST API Reference
- `POST /swarms`: Create governed swarm
- `GET /swarms`: List swarms
- `GET /swarms/{id}`: Get swarm details & budget consumption
- `POST /swarms/{id}/plan`: Generate swarm topology plan
- `POST /swarms/{id}/start`: Start execution
- `POST /swarms/{id}/execute-subtask`: Execute agent subtask
- `POST /swarms/{id}/messages`: Send structured inter-agent message
- `GET /swarms/{id}/messages`: List inter-agent messages
- `POST /swarms/{id}/pause`: Governed pause
- `POST /swarms/{id}/resume`: Governed resume
- `POST /swarms/{id}/cancel`: Governed cancel
- `POST /swarms/{id}/complete`: Aggregate results & verify completion
- `GET /swarms/{id}/metrics`: Swarm telemetry metrics
