"""CheckpointManager — save and restore vessel state."""

from __future__ import annotations

import time
import copy
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Checkpoint:
    """A saved snapshot of vessel state."""
    id: str
    vessel_id: str
    vessel_state: str
    container_snapshot: dict
    tag: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "vessel_id": self.vessel_id,
            "vessel_state": self.vessel_state,
            "container_snapshot": copy.deepcopy(self.container_snapshot),
            "tag": self.tag,
            "created_at": self.created_at,
        }


@dataclass
class CheckpointManager:
    """Manages checkpoint save/load for a vessel.

    In-memory by default. For persistence, the `store` dict can be
    swapped for a persistent backend.
    """

    vessel_id: str
    _store: dict[str, Checkpoint] = field(default_factory=dict, repr=False)
    _counter: int = field(default=0, repr=False)

    def save(
        self,
        state: object,  # VesselState enum
        container_snapshot: dict,
        tag: str = "",
    ) -> str:
        """Save a checkpoint and return its ID.

        Args:
            state: Current vessel state (enum with .value).
            container_snapshot: Serialized container state.
            tag: Optional human-readable label.

        Returns:
            The checkpoint ID.
        """
        self._counter += 1
        state_value = state.value if hasattr(state, "value") else str(state)
        cp_id = f"cp-{self.vessel_id[:8]}-{self._counter:04d}"

        checkpoint = Checkpoint(
            id=cp_id,
            vessel_id=self.vessel_id,
            vessel_state=state_value,
            container_snapshot=copy.deepcopy(container_snapshot),
            tag=tag,
        )
        self._store[cp_id] = checkpoint
        return cp_id

    def load(self, checkpoint_id: str) -> Optional[dict]:
        """Load a checkpoint by ID.

        Returns:
            Checkpoint data dict, or None if not found.
        """
        cp = self._store.get(checkpoint_id)
        if cp is None:
            return None
        return cp.to_dict()

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint. Returns True if it existed."""
        if checkpoint_id in self._store:
            del self._store[checkpoint_id]
            return True
        return False

    def list_checkpoints(self, tag: str | None = None) -> list[dict]:
        """List all checkpoints, optionally filtered by tag.

        Returns:
            List of checkpoint data dicts, newest first.
        """
        checkpoints = list(self._store.values())
        if tag is not None:
            checkpoints = [cp for cp in checkpoints if cp.tag == tag]
        # Sort newest first
        checkpoints.sort(key=lambda cp: cp.created_at, reverse=True)
        return [cp.to_dict() for cp in checkpoints]

    def get_latest(self) -> Optional[dict]:
        """Return the most recent checkpoint, or None."""
        if not self._store:
            return None
        latest = max(self._store.values(), key=lambda cp: cp.created_at)
        return latest.to_dict()

    def count(self) -> int:
        """Return number of stored checkpoints."""
        return len(self._store)

    def clear(self) -> int:
        """Remove all checkpoints. Returns the count cleared."""
        n = len(self._store)
        self._store.clear()
        self._counter = 0
        return n

    def prune(self, keep: int = 5) -> int:
        """Keep only the N newest checkpoints. Returns number pruned.

        Args:
            keep: Number of newest checkpoints to retain.

        Returns:
            Number of checkpoints removed.
        """
        if len(self._store) <= keep:
            return 0
        sorted_cps = sorted(self._store.values(), key=lambda cp: cp.created_at, reverse=True)
        to_keep = {cp.id for cp in sorted_cps[:keep]}
        to_remove = [cp_id for cp_id in self._store if cp_id not in to_keep]
        for cp_id in to_remove:
            del self._store[cp_id]
        return len(to_remove)

    def status(self) -> dict:
        """Return checkpoint manager status."""
        return {
            "vessel_id": self.vessel_id,
            "checkpoint_count": self.count(),
            "checkpoints": [cp["id"] for cp in self.list_checkpoints()],
        }
