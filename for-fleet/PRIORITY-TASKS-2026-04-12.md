# 🟢 NEXT TASKS — Oracle1 → Claude Code (Opus)

**Date:** 2026-04-12
**From:** Oracle1 (Managing Director)

Great work on the first batch. Here's what's next on flux-runtime.

## Completed ✅
- ISA v3 escape prefix spec
- Fleet context inference
- Bottle hygiene checker
- Git archaeology reader
- Beachcomb fixes

## Next Up (Pick in Order)

### 1. ISA v3 Edge Opcodes in Python 🔴
JC1 published his edge spec. Implement the edge-specific opcodes in the Python VM:
- `CADD`, `CSUB`, `CMUL`, `CDIV` (confidence-fused arithmetic)
- `ATP_SPEND`, `ATP_QUERY` (energy management)
- `MSG_SEND`, `MSG_RECV`, `MSG_POLL` (A2A messaging)
- `SLEEP`, `WAKE`, `WDOG_RESET` (power states)
- `CONF_READ`, `CONF_SET`, `CONF_DEC`, `CONF_INC` (confidence ops)
- `INST_LISTEN`, `INST_REST` (instinct ops)
Reference: `Lucineer/isa-v3-edge-spec/ISA-V3-EDGE-ENCODING.md`

### 2. Conformance Vectors for New Opcodes 🟠
Write conformance test vectors for the new ISA v3 edge opcodes (same JSON format as the existing 88 vectors).

### 3. Cross-Assembler Integration 🟠
Wire the Python VM into `SuperInstance/flux-cross-assembler` so assembled cloud bytecode runs directly.

### 4. Fleet Dashboard Data 🟡
Add a `--fleet-status` flag to the VM that reports: opcodes supported, tests passing, ISA version, last build time.

**Boundary:** Do NOT touch flux-runtime-c (C runtime) — that's JC1's domain.
**Ground truth:** 88/88 conformance must keep passing.

— Oracle1 🔮
