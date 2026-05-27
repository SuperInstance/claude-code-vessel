"""Vessel — top-level lifecycle manager for containerized code execution."""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .container import Container, ResourceLimits
from .runtime import Runtime
from .sandbox import Sandbox, SandboxPolicy
from .checkpoint import CheckpointManager


class VesselState(Enum):
    """Lifecycle states for a vessel."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    DESTROYED = "destroyed"
    ERROR = "error"


@dataclass
class VesselConfig:
    """Configuration for creating a new vessel."""
    name: str = ""
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    sandbox_policy: SandboxPolicy = field(default_factory=SandboxPolicy)
    working_directory: str = "/workspace"
    environment: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class Vessel:
    """A containerized execution environment for a code agent.

    Lifecycle: create → run → (pause/resume)* → stop → destroy
    """

    config: VesselConfig = field(default_factory=VesselConfig)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    state: VesselState = VesselState.CREATED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None

    # Internal components (lazy-initialized)
    _container: Optional[Container] = field(default=None, repr=False)
    _runtime: Optional[Runtime] = field(default=None, repr=False)
    _sandbox: Optional[Sandbox] = field(default=None, repr=False)
    _checkpoint_manager: Optional[CheckpointManager] = field(default=None, repr=False)
    _error_message: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.config.name:
            self.config.name = f"vessel-{self.id}"

    @property
    def container(self) -> Container:
        if self._container is None:
            self._container = Container(
                vessel_id=self.id,
                resource_limits=self.config.resource_limits,
                working_directory=self.config.working_directory,
                environment=self.config.environment,
            )
        return self._container

    @property
    def runtime(self) -> Runtime:
        if self._runtime is None:
            self._runtime = Runtime(container=self.container)
        return self._runtime

    @property
    def sandbox(self) -> Sandbox:
        if self._sandbox is None:
            self._sandbox = Sandbox(
                vessel_id=self.id,
                policy=self.config.sandbox_policy,
                working_directory=self.config.working_directory,
            )
        return self._sandbox

    @property
    def checkpoint_manager(self) -> CheckpointManager:
        if self._checkpoint_manager is None:
            self._checkpoint_manager = CheckpointManager(vessel_id=self.id)
        return self._checkpoint_manager

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    @property
    def uptime(self) -> float:
        """Seconds since the vessel was started (0 if not started)."""
        if self.started_at is None:
            return 0.0
        end = self.stopped_at if self.stopped_at else time.time()
        return end - self.started_at

    def _validate_transition(self, target: VesselState) -> None:
        """Check that the state transition is legal."""
        allowed: dict[VesselState, set[VesselState]] = {
            VesselState.CREATED: {VesselState.RUNNING, VesselState.DESTROYED},
            VesselState.RUNNING: {VesselState.PAUSED, VesselState.STOPPED, VesselState.ERROR},
            VesselState.PAUSED: {VesselState.RUNNING, VesselState.STOPPED, VesselState.DESTROYED},
            VesselState.STOPPED: {VesselState.RUNNING, VesselState.DESTROYED},
            VesselState.ERROR: {VesselState.STOPPED, VesselState.DESTROYED},
            VesselState.DESTROYED: set(),
        }
        if target not in allowed.get(self.state, set()):
            raise ValueError(
                f"Cannot transition from {self.state.value} to {target.value}"
            )

    def run(self) -> None:
        """Start the vessel — initializes container, sandbox, and runtime."""
        self._validate_transition(VesselState.RUNNING)
        try:
            self.container.create()
            self.container.start()
            self.sandbox.setup()
            self.state = VesselState.RUNNING
            self.started_at = time.time()
        except Exception as exc:
            self.state = VesselState.ERROR
            self._error_message = str(exc)
            raise

    def pause(self) -> None:
        """Pause execution — container stays alive but frozen."""
        self._validate_transition(VesselState.PAUSED)
        self.container.freeze()
        self.state = VesselState.PAUSED

    def resume(self) -> None:
        """Resume a paused vessel."""
        self._validate_transition(VesselState.RUNNING)
        self.container.unfreeze()
        self.state = VesselState.RUNNING

    def stop(self) -> None:
        """Gracefully stop the vessel."""
        self._validate_transition(VesselState.STOPPED)
        if self._container is not None:
            self.container.stop()
        self.state = VesselState.STOPPED
        self.stopped_at = time.time()

    def destroy(self) -> None:
        """Tear down all resources. Vessel cannot be reused."""
        self._validate_transition(VesselState.DESTROYED)
        if self._container is not None:
            self.container.destroy()
        if self._sandbox is not None:
            self.sandbox.teardown()
        self.state = VesselState.DESTROYED
        self.stopped_at = self.stopped_at or time.time()

    def execute(self, code: str, language: str | None = None) -> dict:
        """Execute code inside the vessel.

        Args:
            code: Source code to execute.
            language: Override language detection (e.g. 'python', 'javascript').

        Returns:
            Dict with 'exit_code', 'stdout', 'stderr', 'duration' keys.
        """
        if self.state != VesselState.RUNNING:
            raise RuntimeError(f"Vessel must be RUNNING to execute code, got {self.state.value}")
        if not self.sandbox.is_file_access_allowed(self.config.working_directory):
            raise PermissionError("Sandbox blocks access to working directory")
        return self.runtime.execute(code, language=language)

    def snapshot(self, tag: str = "") -> str:
        """Create a named checkpoint of current vessel state."""
        if self.state not in (VesselState.RUNNING, VesselState.PAUSED):
            raise RuntimeError(f"Cannot snapshot in state {self.state.value}")
        return self.checkpoint_manager.save(
            state=self.state,
            container_snapshot=self.container.snapshot() if self._container else {},
            tag=tag,
        )

    def restore(self, checkpoint_id: str) -> None:
        """Restore vessel to a previously saved checkpoint."""
        cp = self.checkpoint_manager.load(checkpoint_id)
        if cp is None:
            raise FileNotFoundError(f"No checkpoint found: {checkpoint_id}")
        self.state = VesselState(cp["vessel_state"])
        if self._container is not None and "container_snapshot" in cp:
            self.container.restore(cp["container_snapshot"])

    def status(self) -> dict:
        """Return a status summary."""
        return {
            "id": self.id,
            "name": self.config.name,
            "state": self.state.value,
            "uptime": self.uptime,
            "created_at": self.created_at,
            "error": self._error_message,
            "labels": self.config.labels,
        }
