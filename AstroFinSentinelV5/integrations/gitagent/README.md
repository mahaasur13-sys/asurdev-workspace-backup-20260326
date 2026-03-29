# GitAgent Integration — Phase 1

## Overview
Adapter for MASFactory ↔ GitAgent compatibility + Pilot AstroAgent package.

## GitAgent Structure (from open-gitagent/gitagent)
```
agent.yaml          # Manifest: identity, skills, tools, compliance
SOUL.md            # Personality
RULES.md           # Behavior constraints  
DUTIES.md          # Role boundaries
skills/            # Skill modules (SKILL.md per skill)
tools/             # Tool definitions
sub_agents/        # Sub-agent packages
workflows/         # Workflow definitions
knowledge/         # RAG knowledge base
memory/           # Persistent memory
hooks/            # Lifecycle hooks
```

## Agent Skills Structure (from agentskills.io)
```
SKILL.md           # Entry point with YAML frontmatter
skills.json        # Optional dependency manifest
scripts/           # Executable scripts
references/        # Documentation
assets/            # Static resources
```

## MASFactory Mapping
| GitAgent | MASFactory |
|----------|------------|
| `agent.yaml` | `Topology.nodes` + roles |
| `SOUL.md` | `Role.instructions` |
| `sub_agents/` | `Role.nodes` (AgentNodes) |
| `workflows/` | `SwitchNode.branches` |
| `memory/` | ReplayBuffer + AuditLog |

## Phase 1 Scope
- [x] Analysis complete (this file)
- [x] GitAgent Adapter (`adapters/gitagent_adapter.py`)
- [x] Pilot AstroAgent package (`astro_agent_synthesis/`)
- [ ] Test export/import cycle

## Pilot Package
`astro_agent_synthesis/` — SynthesisAgent as a GitAgent package:
- agent.yaml
- SOUL.md  
- RULES.md
- sub_agents/synthesis_role/
