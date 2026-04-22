# TOOLS.md — Fleet Tool Reference

## Your Tools (on Oracle Cloud ARM64)
- **kimi-cli** v1.37.0 → `/home/ubuntu/.local/bin/kimi-cli` — deep reasoning (kimi-k2.5)
  - `kimi-cli --work-dir <dir>` for workspace-specific work
  - `echo "task" | kimi-cli --work-dir <dir>` for non-interactive
- **Claude Code** v2.1 → `claude` — you ARE this tool
- **crush** v0.56.0 → `crush` — quick patches, scaffolding
- **aider** v0.86.2 → `aider` — test generation, code chat (DeepSeek backend)

## API Keys (in ~/.bashrc)
- **Groq**: `$GROQ_API_KEY` — 24ms inference, high-frequency iterations
- **DeepInfra**: `$DEEPINFRA_API_KEY` — Seed-2.0-mini, creative models
- **SiliconFlow**: `$SILICONFLOW_API_KEY` — DeepSeek, Qwen
- **DeepSeek Direct**: `$DEEPSEEK_API_KEY` — reasoner + chat
- **Moonshot**: `$MOONSHOT_API_KEY` — kimi-k2.5

> Keys are in the environment. Reference by variable name, never hardcode.

## IMPORTANT
- **Groq requires `User-Agent: curl/7.88` header** — Python's default gets 403
- **Kimi K2.5 requires temp ≥ 1.0** — fails at lower temps
- **kimi-cli and Claude Code CANNOT run simultaneously on ARM64** — run sequentially
- **0.7 is universal temperature sweet spot** for most models
