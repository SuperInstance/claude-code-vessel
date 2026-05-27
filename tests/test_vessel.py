"""Tests for the claude_code_vessel package."""

import pytest
import time

from claude_code_vessel import (
    Vessel, VesselState,
    Container, ContainerState, ResourceLimits,
    Runtime, Language,
    Sandbox, SandboxPolicy,
    CheckpointManager,
)
from claude_code_vessel.vessel import VesselConfig


# ── Container Tests ──────────────────────────────────────────

class TestResourceLimits:
    def test_defaults(self):
        r = ResourceLimits()
        assert r.cpu_cores == 2.0
        assert r.memory_mb == 512
        assert r.disk_mb == 1024
        assert r.network_enabled is False

    def test_custom(self):
        r = ResourceLimits(cpu_cores=4.0, memory_mb=2048, network_enabled=True)
        assert r.cpu_cores == 4.0
        assert r.memory_mb == 2048
        assert r.network_enabled is True


class TestContainer:
    def test_create(self):
        c = Container(vessel_id="test-1")
        assert c.state == ContainerState.ABSENT
        c.create()
        assert c.state == ContainerState.CREATED
        assert c.created_at is not None

    def test_lifecycle(self):
        c = Container(vessel_id="test-2")
        c.create()
        c.start()
        assert c.state == ContainerState.RUNNING
        assert c.pid is not None
        c.freeze()
        assert c.state == ContainerState.FROZEN
        c.unfreeze()
        assert c.state == ContainerState.RUNNING
        c.stop()
        assert c.state == ContainerState.STOPPED
        assert c.pid is None

    def test_destroy(self):
        c = Container(vessel_id="test-3")
        c.create()
        c.start()
        c.stop()
        c.destroy()
        assert c.state == ContainerState.DESTROYED

    def test_destroy_idempotent(self):
        c = Container(vessel_id="test-3b")
        c.destroy()  # ABSENT → idempotent
        assert c.state == ContainerState.DESTROYED

    def test_invalid_transition(self):
        c = Container(vessel_id="test-4")
        with pytest.raises(RuntimeError, match="Cannot start"):
            c.start()  # ABSENT can't start

    def test_filesystem(self):
        c = Container(vessel_id="test-5")
        c.create()
        c.write_file("/workspace/hello.py", "print('hi')")
        assert c.read_file("/workspace/hello.py") == "print('hi')"
        assert "/workspace/hello.py" in c.list_files()
        assert len(c.list_files(prefix="/workspace/")) == 1

    def test_filesystem_not_created(self):
        c = Container(vessel_id="test-6")
        with pytest.raises(RuntimeError):
            c.write_file("/foo", "bar")

    def test_filesystem_not_found(self):
        c = Container(vessel_id="test-7")
        c.create()
        with pytest.raises(FileNotFoundError):
            c.read_file("/nonexistent")

    def test_snapshot_restore(self):
        c = Container(vessel_id="test-8")
        c.create()
        c.start()
        c.write_file("/workspace/data.txt", "important")
        snap = c.snapshot()
        assert snap["state"] == "running"
        assert "/workspace/data.txt" in snap["fs"]
        # Restore into a fresh container
        c2 = Container(vessel_id="test-8b")
        c2.restore(snap)
        assert c2.state == ContainerState.RUNNING
        assert c2.read_file("/workspace/data.txt") == "important"

    def test_resource_usage(self):
        c = Container(vessel_id="test-9")
        c.create()
        c.start()
        usage = c.resource_usage()
        assert "cpu_percent" in usage
        assert "memory_used_mb" in usage

    def test_resource_usage_not_running(self):
        c = Container(vessel_id="test-10")
        assert c.resource_usage() == {}

    def test_status(self):
        c = Container(vessel_id="test-11")
        c.create()
        s = c.status()
        assert s["vessel_id"] == "test-11"
        assert s["state"] == "created"


# ── Runtime Tests ────────────────────────────────────────────

class TestLanguageDetection:
    def setup_method(self):
        self.runtime = Runtime(container=None)

    def test_python_detection(self):
        assert self.runtime.detect_language("import os\nprint('hello')") == Language.PYTHON

    def test_python_class(self):
        assert self.runtime.detect_language("class Foo:\n    pass") == Language.PYTHON

    def test_javascript_detection(self):
        assert self.runtime.detect_language("const x = 42;\nconsole.log(x)") == Language.JAVASCRIPT

    def test_typescript_detection(self):
        code = "interface User { name: string; age: number; }"
        assert self.runtime.detect_language(code) == Language.TYPESCRIPT

    def test_bash_detection(self):
        assert self.runtime.detect_language("#!/bin/bash\necho hello") == Language.BASH

    def test_rust_detection(self):
        assert self.runtime.detect_language("fn main() {\n    println!(\"hello\");\n}") == Language.RUST

    def test_go_detection(self):
        assert self.runtime.detect_language("package main\nfunc main() {}") == Language.GO

    def test_ruby_detection(self):
        assert self.runtime.detect_language("def hello\n  puts 'hi'\nend") == Language.RUBY

    def test_empty_code(self):
        assert self.runtime.detect_language("") == Language.UNKNOWN
        assert self.runtime.detect_language("   \n  ") == Language.UNKNOWN

    def test_unknown_code(self):
        assert self.runtime.detect_language("asdf qwer zxcv") == Language.UNKNOWN


class TestExecution:
    def setup_method(self):
        c = Container(vessel_id="exec-test")
        c.create()
        self.runtime = Runtime(container=c)

    def test_python_print(self):
        result = self.runtime.execute("print('hello world')")
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]
        assert result["language"] == "python"

    def test_python_multiple_prints(self):
        code = "print('line1')\nprint('line2')\nprint('line3')"
        result = self.runtime.execute(code)
        assert result["exit_code"] == 0
        assert "line1" in result["stdout"]
        assert "line3" in result["stdout"]

    def test_python_raise(self):
        result = self.runtime.execute("raise Exception('oops')")
        assert result["exit_code"] == 1

    def test_javascript_execution(self):
        code = "console.log('hello from js');"
        result = self.runtime.execute(code)
        assert result["exit_code"] == 0
        assert "hello from js" in result["stdout"]
        assert result["language"] == "javascript"

    def test_bash_execution(self):
        code = "#!/bin/bash\necho hello bash"
        result = self.runtime.execute(code)
        assert result["exit_code"] == 0
        assert "hello bash" in result["stdout"]

    def test_language_override(self):
        result = self.runtime.execute("random text", language="python")
        assert result["language"] == "python"

    def test_empty_code(self):
        result = self.runtime.execute("")
        assert result["exit_code"] == 0
        assert result["stdout"] == ""

    def test_execution_count(self):
        self.runtime.execute("print('a')")
        self.runtime.execute("print('b')")
        info = self.runtime.info()
        assert info["execution_count"] == 2

    def test_result_has_duration(self):
        result = self.runtime.execute("print('timed')")
        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], float)

    def test_success_property(self):
        result = self.runtime.execute("print('ok')")
        assert result["success"] is True


# ── Sandbox Tests ────────────────────────────────────────────

class TestSandboxPolicy:
    def test_defaults(self):
        p = SandboxPolicy()
        assert p.network_enabled is False
        assert "/workspace" in p.allowed_paths
        assert p.max_file_size_bytes == 10 * 1024 * 1024


class TestSandbox:
    def test_setup_teardown(self):
        s = Sandbox(vessel_id="sb-1")
        assert not s.is_active
        s.setup()
        assert s.is_active
        s.teardown()
        assert not s.is_active

    def test_file_access_allowed(self):
        s = Sandbox(vessel_id="sb-2")
        s.setup()
        assert s.is_file_access_allowed("/workspace/main.py")
        assert s.is_file_access_allowed("/tmp/output.log")

    def test_file_access_blocked_path(self):
        s = Sandbox(vessel_id="sb-3")
        s.setup()
        assert not s.is_file_access_allowed("/etc/shadow")
        assert not s.is_file_access_allowed("/root/.ssh/id_rsa")
        assert s.violation_count == 2

    def test_file_access_blocked_extension(self):
        s = Sandbox(vessel_id="sb-4")
        s.setup()
        assert not s.is_file_access_allowed("/workspace/malware.exe")

    def test_file_access_not_in_allowed(self):
        s = Sandbox(vessel_id="sb-5")
        s.setup()
        assert not s.is_file_access_allowed("/opt/secret/data.txt")

    def test_network_disabled(self):
        s = Sandbox(vessel_id="sb-6")
        s.setup()
        assert not s.is_network_access_allowed("google.com", 443)
        assert s.violation_count == 1

    def test_network_enabled(self):
        policy = SandboxPolicy(network_enabled=True, allow_network_access=True)
        s = Sandbox(vessel_id="sb-7", policy=policy)
        s.setup()
        assert s.is_network_access_allowed("example.com", 443)

    def test_network_blocked_hosts(self):
        policy = SandboxPolicy(network_enabled=True, allow_network_access=True)
        s = Sandbox(vessel_id="sb-8", policy=policy)
        s.setup()
        assert not s.is_network_access_allowed("169.254.169.254", 80)

    def test_network_allowed_hosts_filter(self):
        policy = SandboxPolicy(
            network_enabled=True,
            allow_network_access=True,
            allowed_hosts=["api.example.com"],
        )
        s = Sandbox(vessel_id="sb-9", policy=policy)
        s.setup()
        assert s.is_network_access_allowed("api.example.com", 443)
        assert not s.is_network_access_allowed("evil.com", 443)

    def test_subprocess_blocked(self):
        s = Sandbox(vessel_id="sb-10")
        s.setup()
        assert not s.is_subprocess_allowed()

    def test_subprocess_allowed(self):
        policy = SandboxPolicy(allow_subprocess=True)
        s = Sandbox(vessel_id="sb-11", policy=policy)
        s.setup()
        assert s.is_subprocess_allowed()

    def test_file_size_check(self):
        s = Sandbox(vessel_id="sb-12")
        s.setup()
        assert s.check_file_size(1024)
        assert not s.check_file_size(100 * 1024 * 1024)

    def test_violations_tracking(self):
        s = Sandbox(vessel_id="sb-13")
        s.setup()
        s.is_file_access_allowed("/etc/shadow")
        assert s.violation_count == 1
        violations = s.violations
        assert violations[0]["kind"] == "file_access_blocked_path"
        s.clear_violations()
        assert s.violation_count == 0

    def test_inactive_sandbox_allows_all(self):
        s = Sandbox(vessel_id="sb-14")
        # Not activated — everything allowed
        assert s.is_file_access_allowed("/etc/shadow")
        assert s.is_network_access_allowed("evil.com", 9999)
        assert s.is_subprocess_allowed()
        assert s.violation_count == 0

    def test_status(self):
        s = Sandbox(vessel_id="sb-15")
        s.setup()
        status = s.status()
        assert status["active"] is True
        assert status["vessel_id"] == "sb-15"


# ── CheckpointManager Tests ──────────────────────────────────

class TestCheckpointManager:
    def test_save_and_load(self):
        cm = CheckpointManager(vessel_id="cp-1")
        cp_id = cm.save(state=VesselState.RUNNING, container_snapshot={"fs": {}}, tag="initial")
        assert cp_id.startswith("cp-")
        loaded = cm.load(cp_id)
        assert loaded is not None
        assert loaded["vessel_state"] == "running"
        assert loaded["tag"] == "initial"

    def test_load_nonexistent(self):
        cm = CheckpointManager(vessel_id="cp-2")
        assert cm.load("nope") is None

    def test_delete(self):
        cm = CheckpointManager(vessel_id="cp-3")
        cp_id = cm.save(state=VesselState.RUNNING, container_snapshot={})
        assert cm.delete(cp_id) is True
        assert cm.load(cp_id) is None
        assert cm.delete(cp_id) is False

    def test_list_checkpoints(self):
        cm = CheckpointManager(vessel_id="cp-4")
        cm.save(state=VesselState.RUNNING, container_snapshot={}, tag="a")
        cm.save(state=VesselState.PAUSED, container_snapshot={}, tag="b")
        cps = cm.list_checkpoints()
        assert len(cps) == 2
        # Newest first
        assert cps[0]["tag"] == "b"

    def test_list_checkpoints_by_tag(self):
        cm = CheckpointManager(vessel_id="cp-5")
        cm.save(state=VesselState.RUNNING, container_snapshot={}, tag="x")
        cm.save(state=VesselState.RUNNING, container_snapshot={}, tag="y")
        assert len(cm.list_checkpoints(tag="x")) == 1

    def test_get_latest(self):
        cm = CheckpointManager(vessel_id="cp-6")
        cm.save(state=VesselState.CREATED, container_snapshot={}, tag="old")
        cm.save(state=VesselState.RUNNING, container_snapshot={}, tag="new")
        latest = cm.get_latest()
        assert latest["tag"] == "new"

    def test_get_latest_empty(self):
        cm = CheckpointManager(vessel_id="cp-7")
        assert cm.get_latest() is None

    def test_count(self):
        cm = CheckpointManager(vessel_id="cp-8")
        assert cm.count() == 0
        cm.save(state=VesselState.RUNNING, container_snapshot={})
        assert cm.count() == 1

    def test_clear(self):
        cm = CheckpointManager(vessel_id="cp-9")
        cm.save(state=VesselState.RUNNING, container_snapshot={})
        cm.save(state=VesselState.RUNNING, container_snapshot={})
        assert cm.clear() == 2
        assert cm.count() == 0

    def test_prune(self):
        cm = CheckpointManager(vessel_id="cp-10")
        for i in range(10):
            cm.save(state=VesselState.RUNNING, container_snapshot={}, tag=f"cp-{i}")
        pruned = cm.prune(keep=3)
        assert pruned == 7
        assert cm.count() == 3

    def test_prune_nothing(self):
        cm = CheckpointManager(vessel_id="cp-11")
        cm.save(state=VesselState.RUNNING, container_snapshot={})
        assert cm.prune(keep=5) == 0

    def test_snapshot_isolation(self):
        """Modifying loaded data doesn't affect stored checkpoint."""
        cm = CheckpointManager(vessel_id="cp-12")
        cp_id = cm.save(state=VesselState.RUNNING, container_snapshot={"key": "value"})
        loaded = cm.load(cp_id)
        loaded["container_snapshot"]["key"] = "mutated"
        reloaded = cm.load(cp_id)
        assert reloaded["container_snapshot"]["key"] == "value"


# ── Vessel Integration Tests ─────────────────────────────────

class TestVessel:
    def test_create_vessel(self):
        v = Vessel()
        assert v.state == VesselState.CREATED
        assert v.id
        assert v.config.name.startswith("vessel-")

    def test_custom_config(self):
        config = VesselConfig(
            name="my-vessel",
            resource_limits=ResourceLimits(cpu_cores=8.0, memory_mb=4096),
            labels={"team": "engineering"},
        )
        v = Vessel(config=config)
        assert v.config.name == "my-vessel"
        assert v.config.resource_limits.cpu_cores == 8.0

    def test_full_lifecycle(self):
        v = Vessel()
        v.run()
        assert v.state == VesselState.RUNNING
        assert v.started_at is not None

        v.pause()
        assert v.state == VesselState.PAUSED

        v.resume()
        assert v.state == VesselState.RUNNING

        v.stop()
        assert v.state == VesselState.STOPPED
        assert v.stopped_at is not None

    def test_destroy_from_created(self):
        v = Vessel()
        v.destroy()
        assert v.state == VesselState.DESTROYED

    def test_destroy_from_stopped(self):
        v = Vessel()
        v.run()
        v.stop()
        v.destroy()
        assert v.state == VesselState.DESTROYED

    def test_invalid_transition(self):
        v = Vessel()
        with pytest.raises(ValueError, match="Cannot transition"):
            v.pause()  # CREATED → PAUSED is invalid

    def test_execute_code(self):
        v = Vessel()
        v.run()
        result = v.execute("print('hello from vessel')")
        assert result["exit_code"] == 0
        assert "hello from vessel" in result["stdout"]

    def test_execute_not_running(self):
        v = Vessel()
        with pytest.raises(RuntimeError, match="must be RUNNING"):
            v.execute("print('oops')")

    def test_uptime(self):
        v = Vessel()
        assert v.uptime == 0.0
        v.run()
        assert v.uptime >= 0
        v.stop()
        assert v.uptime >= 0

    def test_status(self):
        v = Vessel()
        s = v.status()
        assert s["state"] == "created"
        assert "id" in s
        assert "name" in s

    def test_error_state(self):
        v = Vessel()
        # Force an error by sabotaging the container
        v._container = None  # Will be recreated
        # We need to make container.create() fail
        original = v.container.create
        v.container.create = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        with pytest.raises(RuntimeError, match="boom"):
            v.run()
        assert v.state == VesselState.ERROR
        assert v.error_message == "boom"

    def test_snapshot_and_restore(self):
        v = Vessel()
        v.run()
        v.execute("print('hello')")

        # Snapshot
        cp_id = v.snapshot(tag="before-change")
        assert cp_id

        # Restore
        v.restore(cp_id)
        assert v.state == VesselState.RUNNING

    def test_snapshot_not_running(self):
        v = Vessel()
        with pytest.raises(RuntimeError, match="Cannot snapshot"):
            v.snapshot()

    def test_restore_nonexistent(self):
        v = Vessel()
        with pytest.raises(FileNotFoundError):
            v.restore("no-such-checkpoint")

    def test_lazy_component_init(self):
        """Components are only created when accessed."""
        v = Vessel()
        assert v._container is None
        assert v._runtime is None
        assert v._sandbox is None
        assert v._checkpoint_manager is None
        # Accessing properties creates them
        assert v.container is not None
        assert v._container is not None


class TestVesselSandboxIntegration:
    def test_sandbox_blocks_execution_if_no_access(self):
        """If sandbox blocks the working directory, execute should fail."""
        policy = SandboxPolicy(allowed_paths=["/other"])  # no /workspace
        config = VesselConfig(
            working_directory="/workspace",
            sandbox_policy=policy,
        )
        v = Vessel(config=config)
        v.run()
        with pytest.raises(PermissionError, match="Sandbox blocks"):
            v.execute("print('blocked')")
