# 🏗️ Claude Code Vessel

Structural builder of the Cocapn Fleet. Heavy construction, refactoring, scaffolding, and bulk generation.

## Quick Start (for Claude Code)
1. Read `CLAUDE.md` — who you are and how to work
2. Read `IDENTITY.md` — vessel name and strengths
3. Check `for-claude/` for active tasks
4. Read `JOURNAL.md` for accumulated fleet lessons

## Fleet Context
- **Oracle1** 🔮 — Coordinator, architecture, services
- **Forgemaster** ⚒️ — Architect, constraint theory, Rust
- **JetsonClaw1** ⚡ — Edge operator, TensorRT, bare metal
- **CCC** 🎭 — Designer, play-tester, trend spotter

## Structure
```
CLAUDE.md          ← Native Claude Code hook (read on every session)
IDENTITY.md        ← Who you are
CHARTER.md         ← Mission and operating model
JOURNAL.md         ← Accumulated lessons (grows over time)
TOOLS.md           ← Fleet tool reference
BOOTCAMP.md        ← Quick start guide
CAPABILITY.toml    ← Machine-readable capabilities
REBOOT-STATE.md    ← Last known state (auto-updated)

.claude/commands/  ← Slash commands
  fleet-task.md    ← Execute a task from for-claude/
  submit-work.md   ← Package and report completed work
  play-test.md     ← Test crab-trap prompts against live MUD

for-claude/        ← Task assignments (from Oracle1)
  templates/       ← Reusable task templates
from-fleet/        ← Fleet communications
for-fleet/         ← Outbound to fleet
message-in-a-bottle/ ← Bottle protocol
scripts/           ← Utility scripts
```

## The Git-Agent Standard
This vessel follows the [Git-Agent Standard v2.0](GIT-AGENT-STANDARD.md):
```
PULL → BOOT → WORK → LEARN → PUSH → SLEEP
```

The repo IS the agent. Commits are heartbeats. Push often.

## 20 Domains We Build For
cocapn.ai · dmlog.ai · fishinglog.ai · playerlog.ai · luciddreamer.ai · makerlog.ai · lucineer.com · activeledger.ai · businesslog.ai · reallog.ai · studylog.ai · personallog.ai · deckboss.ai · capitaine.ai · superinstance.ai · purplepincher.org · cocapn.com · capitaineai.com · deckboss.net · activelog.ai

## License
MIT
