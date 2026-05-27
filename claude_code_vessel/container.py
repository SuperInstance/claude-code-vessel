"""Container — resource-limited execution container with isolation and snapshots."""

from __future__ import annotations

import time
import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContainerState(Enum):
    ABSENT = "absent"
    CREATED = "created"
    RUNNING = "running"
    FROZEN = "frozen"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


@dataclass
class ResourceLimits:
    """Resource constraints for a container."""
    cpu_cores: float = 2.0
    memory_mb: int = 512
    disk_mb: int = 1024
    max_processes: int = 64
    network_enabled: bool = False
    timeout_seconds: int = 300


@dataclass
class Container:
    """A lightweight container abstraction with resource limits and snapshots.

    This is a simulation / in-memory model — real container runtimes
    (Docker, containerd, etc.) would plug in behind this interface.
    """

    vessel_id: str
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    working_directory: str = "/workspace"
    environment: dict[str, str] = field(default_factory=dict)
    state: ContainerState = ContainerState.ABSENT
    pid: Optional[int] = None
    created_at: Optional[float] = None
    _snapshot_data: Optional[dict] = field(default=None, repr=False)
    _fs: dict = field(default_factory=dict, repr=False)  # simulated filesystem

    def create(self) -> None:
        """Create the container filesystem and prepare for execution."""
        if self.state not in (ContainerState.ABSENT, ContainerState.DESTROYED):
            raise RuntimeError(f"Cannot create from state {self.state.value}")
        self._fs = {
            self.working_directory: {},
            "/tmp": {},
            "/proc": {},
        }
        self.state = ContainerState.CREATED
        self.created_at = time.time()

    def start(self) -> None:
        """Start the container's init process."""
        if self.state not in (ContainerState.CREATED, ContainerState.STOPPED):
            raise RuntimeError(f"Cannot start from state {self.state.value}")
        self.state = ContainerState.RUNNING
        self.pid = hash(self.vessel_id) % 65535 + 1  # simulated PID

    def freeze(self) -> None:
        """Freeze (pause) the container."""
        if self.state != ContainerState.RUNNING:
            raise RuntimeError(f"Cannot freeze from state {self.state.value}")
        self.state = ContainerState.FROZEN

    def unfreeze(self) -> None:
        """Unfreeze (resume) the container."""
        if self.state != ContainerState.FROZEN:
            raise RuntimeError(f"Cannot unfreeze from state {self.state.value}")
        self.state = ContainerState.RUNNING

    def stop(self) -> None:
        """Stop the container (processes killed, filesystem preserved)."""
        if self.state in (ContainerState.STOPPED, ContainerState.DESTROYED, ContainerState.ABSENT):
            raise RuntimeError(f"Cannot stop from state {self.state.value}")
        self.state = ContainerState.STOPPED
        self.pid = None

    def destroy(self) -> None:
        """Destroy the container — all resources released."""
        if self.state == ContainerState.DESTROYED:
            return  # idempotent
        self.state = ContainerState.DESTROYED
        self.pid = None
        self._fs.clear()
        self._snapshot_data = None

    def write_file(self, path: str, content: str) -> None:
        """Write a file into the simulated container filesystem."""
        if self.state in (ContainerState.ABSENT, ContainerState.DESTROYED):
            raise RuntimeError("Container not available for writes")
        self._fs[path] = content

    def read_file(self, path: str) -> str:
        """Read a file from the simulated container filesystem."""
        if path not in self._fs:
            raise FileNotFoundError(f"No such file: {path}")
        return self._fs[path]

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in the simulated filesystem, optionally filtered by prefix."""
        if prefix:
            return [p for p in self._fs if p.startswith(prefix)]
        return list(self._fs.keys())

    def snapshot(self) -> dict:
        """Capture container state for later restore."""
        if self.state == ContainerState.ABSENT:
            raise RuntimeError("Nothing to snapshot")
        self._snapshot_data = {
            "state": self.state.value,
            "fs": copy.deepcopy(self._fs),
            "environment": copy.deepcopy(self.environment),
            "resource_limits": {
                "cpu_cores": self.resource_limits.cpu_cores,
                "memory_mb": self.resource_limits.memory_mb,
                "disk_mb": self.resource_limits.disk_mb,
                "max_processes": self.resource_limits.max_processes,
                "network_enabled": self.resource_limits.network_enabled,
                "timeout_seconds": self.resource_limits.timeout_seconds,
            },
            "timestamp": time.time(),
        }
        return self._snapshot_data

    def restore(self, data: dict) -> None:
        """Restore container from a previously captured snapshot."""
        self.state = ContainerState(data["state"])
        self._fs = copy.deepcopy(data.get("fs", {}))
        self.environment = copy.deepcopy(data.get("environment", {}))
        self._snapshot_data = data

    def resource_usage(self) -> dict:
        """Report current resource usage (simulated)."""
        if self.state not in (ContainerState.RUNNING, ContainerState.FROZEN):
            return {}
        return {
            "cpu_percent": min(85.0, self.resource_limits.cpu_cores * 42),
            "memory_used_mb": min(
                self.resource_limits.memory_mb - 16,
                len(self._fs) * 4 + 32,
            ),
            "disk_used_mb": min(
                self.resource_limits.disk_mb,
                sum(len(str(v)) for v in self._fs.values()) // 1024 + 8,
            ),
            "processes": min(self.resource_limits.max_processes, 3 + len(self._fs) // 10),
        }

    def status(self) -> dict:
        """Return a summary of container state."""
        return {
            "vessel_id": self.vessel_id,
            "state": self.state.value,
            "pid": self.pid,
            "created_at": self.created_at,
            "working_directory": self.working_directory,
            "limits": {
                "cpu": f"{self.resource_limits.cpu_cores} cores",
                "memory": f"{self.resource_limits.memory_mb} MB",
                "disk": f"{self.resource_limits.disk_mb} MB",
            },
        }
