# claude-code-vessel — Containerized Execution for Code Agents

**Structural builder of the Cocapn Fleet. Containerized runtimes, sandboxed execution, checkpoints.**

## What This Gives You

- **Vessels** — managed execution environments with lifecycle states (CREATING → READY → RUNNING → STOPPED)
- **Containers** — resource-limited isolation with CPU, memory, and time constraints
- **Multi-language runtimes** — Python, Rust, TypeScript, Go, Shell execution
- **Sandbox policies** — configurable security: network access, filesystem access, execution limits
- **Checkpoints** — save and restore vessel state for resumable work

## Quick Start

```python
from claude_code_vessel import Vessel, Container, Runtime, Sandbox, SandboxPolicy

# Create a sandboxed vessel
policy = SandboxPolicy(
    allow_network=False,
    allow_filesystem_write=True,
    max_execution_time_seconds=300,
    max_memory_mb=512,
)
vessel = Vessel(
    name="readme-rewriter",
    container=Container(runtime=Runtime.PYTHON, resource_limits=ResourceLimits(memory_mb=512)),
    sandbox=Sandbox(policy=policy),
)

# Run code in isolation
vessel.start()
result = vessel.execute("print('Hello from vessel')")
print(result.output)  # "Hello from vessel"

# Checkpoint and restore
vessel.checkpoint("after-setup")
vessel.stop()
# Later...
vessel.restore("after-setup")
```

## API Reference

### `Vessel(name, container, sandbox=None)`
Managed execution environment with lifecycle management.

### `Container(runtime, resource_limits)`
`Runtime`: PYTHON, RUST, TYPESCRIPT, GO, SHELL
`ResourceLimits`: cpu_cores, memory_mb, disk_mb, time_seconds

### `Sandbox(policy=SandboxPolicy(...))`
`SandboxPolicy`: allow_network, allow_filesystem_write, allow_subprocess, max_execution_time_seconds, max_memory_mb

### `CheckpointManager`
Save/restore vessel state snapshots.

## How It Fits

The heavy construction vessel of the [SuperInstance fleet](https://github.com/SuperInstance). Handles refactoring, scaffolding, bulk generation, and any work that needs isolated execution.

- **[cocapn](https://github.com/SuperInstance/cocapn)** — Core agent infrastructure
- **[branch-sandbox](https://github.com/SuperInstance/branch-sandbox)** — Branch-level isolation
- **[cicd-agent](https://github.com/SuperInstance/cicd-agent)** — CI/CD pipeline (dispatches to vessels)
- **[cartridge-agent](https://github.com/SuperInstance/cartridge-agent)** — Swappable behavior cartridges

## Testing

```bash
pytest tests/
```

Python 3.10+. MIT license.
