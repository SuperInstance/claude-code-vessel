"""Sandbox — file isolation and network restrictions for vessel execution."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SandboxPolicy:
    """Policy governing what a sandboxed vessel can access."""
    # Filesystem rules
    allowed_paths: list[str] = field(default_factory=lambda: ["/workspace", "/tmp"])
    blocked_paths: list[str] = field(default_factory=lambda: ["/etc/shadow", "/etc/passwd", "/root"])
    allowed_extensions: list[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".sh", ".rs", ".go", ".rb",
        ".txt", ".md", ".json", ".yaml", ".yml", ".toml",
        ".csv", ".log",
    ])
    blocked_extensions: list[str] = field(default_factory=lambda: [
        ".exe", ".dll", ".so", ".dylib", ".bin",
    ])
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB

    # Network rules
    network_enabled: bool = False
    allowed_hosts: list[str] = field(default_factory=list)  # empty = none when network_enabled=False
    blocked_hosts: list[str] = field(default_factory=lambda: [
        "metadata.google.internal",
        "169.254.169.254",  # cloud metadata endpoints
    ])
    allowed_ports: list[int] = field(default_factory=lambda: [80, 443])

    # Execution rules
    allow_subprocess: bool = False
    allow_network_access: bool = False
    max_open_files: int = 64


@dataclass
class Sandbox:
    """Sandbox enforcing file isolation and network restrictions.

    All access checks go through the policy. The sandbox tracks
    violations for audit purposes.
    """

    vessel_id: str
    policy: SandboxPolicy = field(default_factory=SandboxPolicy)
    working_directory: str = "/workspace"
    _violations: list[dict] = field(default_factory=list, repr=False)
    _active: bool = field(default=False, repr=False)

    def setup(self) -> None:
        """Initialize sandbox restrictions."""
        self._active = True
        self._violations.clear()

    def teardown(self) -> None:
        """Remove sandbox restrictions."""
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def is_file_access_allowed(self, path: str) -> bool:
        """Check if a file path is accessible under the sandbox policy.

        A path is allowed if:
        1. It matches an allowed_paths prefix (or allowed_paths is empty = all allowed)
        2. It does NOT match a blocked_paths entry
        3. Its extension is in allowed_extensions (or no extension)
        4. Its extension is NOT in blocked_extensions
        """
        if not self._active:
            return True

        # Check blocked paths first (deny takes priority)
        for blocked in self.policy.blocked_paths:
            if path.startswith(blocked) or fnmatch.fnmatch(path, blocked + "/*"):
                self._log_violation("file_access_blocked_path", path)
                return False

        # Check allowed paths (if specified, path must match at least one)
        if self.policy.allowed_paths:
            if not any(path.startswith(allowed) or fnmatch.fnmatch(path, allowed + "/*")
                       for allowed in self.policy.allowed_paths):
                self._log_violation("file_access_not_in_allowed", path)
                return False

        # Check extension blocklist
        for ext in self.policy.blocked_extensions:
            if path.endswith(ext):
                self._log_violation("file_access_blocked_extension", path)
                return False

        # Check extension allowlist (only if specified)
        if self.policy.allowed_extensions:
            # Allow paths without extensions (directories, etc.)
            if "." in path.split("/")[-1]:
                ext = "." + path.rsplit(".", 1)[-1]
                if ext not in self.policy.allowed_extensions:
                    self._log_violation("file_access_extension_not_allowed", path)
                    return False

        return True

    def is_network_access_allowed(self, host: str = "", port: int = 0) -> bool:
        """Check if network access to host:port is permitted."""
        if not self._active:
            return True

        if not self.policy.network_enabled:
            self._log_violation("network_disabled", f"{host}:{port}")
            return False

        if not self.policy.allow_network_access:
            self._log_violation("network_not_allowed", f"{host}:{port}")
            return False

        # Check blocked hosts
        for blocked in self.policy.blocked_hosts:
            if host == blocked or host.endswith("." + blocked):
                self._log_violation("network_blocked_host", host)
                return False

        # Check allowed hosts (if specified, must match)
        if self.policy.allowed_hosts:
            if not any(host == allowed or host.endswith("." + allowed)
                       for allowed in self.policy.allowed_hosts):
                self._log_violation("network_host_not_allowed", host)
                return False

        # Check port
        if port and self.policy.allowed_ports:
            if port not in self.policy.allowed_ports:
                self._log_violation("network_port_not_allowed", str(port))
                return False

        return True

    def is_subprocess_allowed(self) -> bool:
        """Check if subprocess creation is permitted."""
        if not self._active:
            return True
        if not self.policy.allow_subprocess:
            self._log_violation("subprocess_blocked", "")
            return False
        return True

    def check_file_size(self, size_bytes: int) -> bool:
        """Check if a file of the given size would be allowed."""
        if size_bytes > self.policy.max_file_size_bytes:
            self._log_violation("file_size_exceeded", f"{size_bytes} > {self.policy.max_file_size_bytes}")
            return False
        return True

    def _log_violation(self, kind: str, detail: str) -> None:
        """Record a sandbox violation."""
        self._violations.append({
            "kind": kind,
            "detail": detail,
            "vessel_id": self.vessel_id,
        })

    @property
    def violations(self) -> list[dict]:
        """Return a copy of recorded violations."""
        return list(self._violations)

    @property
    def violation_count(self) -> int:
        return len(self._violations)

    def clear_violations(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()

    def status(self) -> dict:
        """Return sandbox status summary."""
        return {
            "active": self._active,
            "vessel_id": self.vessel_id,
            "policy": {
                "network_enabled": self.policy.network_enabled,
                "allow_subprocess": self.policy.allow_subprocess,
                "allowed_paths": self.policy.allowed_paths,
                "blocked_paths": self.policy.blocked_paths,
            },
            "violation_count": self.violation_count,
        }
