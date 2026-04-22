# Task: Add Domain Rooms — [DOMAIN]

## Priority: 🟡 Medium

## Objective
Add themed PLATO rooms for a new domain to `scripts/domain-rooms.py`.

## Domain: [domain.ai]
- **Theme**: [what this domain is about]
- **Purpose**: [what users do here]

## Room Requirements
Each room needs:
- Unique `name` with emoji prefix (e.g., "🍺 The Rusty Anchor")
- `tagline` (short, evocative)
- `description` (2-3 sentences, immersive)
- 5-8 `objects`, each with a detailed description (1-2 sentences explaining the ML/tech metaphor)
- 3-5 `exits` to other rooms in this domain

## Design Principles
- Every object should map to a real concept (not just decoration)
- Descriptions should make agents WANT to interact
- Exits should create a natural exploration flow (hub → branches → return)
- The room should work for both humans (browser PLATO) and AI agents (API consumers)

## File to Modify
`SuperInstance/oracle1-workspace/scripts/domain-rooms.py` → add to `DOMAIN_ROOMS` dict

## Acceptance Criteria
- Room renders correctly via `/domain.ai/room/room-name`
- All objects are examinable via `/interact?agent=X&room=Y&target=Z`
- Exits point to real rooms (no dead ends)
- 5+ objects per room, each with meaningful descriptions
