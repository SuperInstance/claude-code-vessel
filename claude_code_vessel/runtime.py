"""Runtime — language detection and code execution within a container."""

from __future__ import annotations

import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    RUST = "rust"
    GO = "go"
    RUBY = "ruby"
    UNKNOWN = "unknown"


# Patterns for language detection from source code
_LANGUAGE_HINTS: dict[Language, list[str]] = {
    Language.PYTHON: [
        r"^\s*(import |from \w+ import |def |class |if __name__|print\s*\()",
        r"^\s*#\s*python",
        r"(?:^|\n)\s*(?:def |class |import |from \w)",
        r"print\([^)]*\)",
        r"(?m)^>>> ",  # REPL-style
        r'\braise\s+\w+Error\b',
        r'\braise\s+Exception\b',
    ],
    Language.JAVASCRIPT: [
        r"(?:const|let|var)\s+\w+\s*=",
        r"(?:function\s+\w+|=>\s*{)",
        r"console\.log\s*\(",
        r"require\s*\(",
        r"(?:^|\n)\s*(?:export|module\.exports)",
    ],
    Language.TYPESCRIPT: [
        r":\s*(?:string|number|boolean|void|any)\s*[=;{)]",
        r"interface\s+\w+",
        r"<\w+>",
        r"as\s+(?:string|number|any)",
    ],
    Language.BASH: [
        r"^#!/bin/(?:ba)?sh",
        r"(?:^|\n)\s*(?:echo|export|cd |ls |grep |awk |sed |chmod |mkdir )",
        r"\$\{?\w+\}?",
        r"(?:^|\n)\s*(?:if|for|while|case)\s+",
    ],
    Language.RUST: [
        r"fn\s+\w+",
        r"let\s+mut\s+",
        r"(?:println!|eprintln!)\s*!",
        r"impl\s+\w+",
        r"use\s+std::",
    ],
    Language.GO: [
        r"func\s+\w+",
        r"package\s+\w+",
        r"fmt\.Print",
        r":=\s*",
        r"go\s+\w+\(",
    ],
    Language.RUBY: [
        r"def\s+\w+",
        r"puts\s+",
        r"require\s+['\"]",
        r"attr_(?:accessor|reader|writer)",
        r"end\s*$",
    ],
}


@dataclass
class ExecutionResult:
    """Result of a code execution."""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    language: Language = Language.UNKNOWN
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "language": self.language.value,
            "timed_out": self.timed_out,
            "success": self.success,
        }


@dataclass
class Runtime:
    """Code execution runtime bound to a container.

    Handles language detection and simulated code execution.
    In production, this would delegate to actual language runtimes
    inside the container.
    """

    container: object  # Container instance (avoid circular import)
    _execution_count: int = field(default=0, repr=False)

    def detect_language(self, code: str) -> Language:
        """Detect the programming language of the given source code.

        Uses pattern matching against known language signatures.
        """
        if not code.strip():
            return Language.UNKNOWN

        scores: dict[Language, int] = {}

        for lang, patterns in _LANGUAGE_HINTS.items():
            score = 0
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, code, re.MULTILINE)
                    score += len(matches)
                except re.error:
                    pass
            if score > 0:
                scores[lang] = score

        if not scores:
            return Language.UNKNOWN

        # TypeScript and JavaScript overlap — prefer TS if it scored
        if Language.TYPESCRIPT in scores and Language.JAVASCRIPT in scores:
            if scores[Language.TYPESCRIPT] >= scores[Language.JAVASCRIPT]:
                return Language.TYPESCRIPT

        return max(scores, key=lambda l: scores[l])

    def execute(self, code: str, language: str | None = None) -> dict:
        """Execute code and return the result.

        Args:
            code: Source code to execute.
            language: Optional language override (e.g. 'python').

        Returns:
            Dict with execution results (matches ExecutionResult fields).
        """
        start = time.time()

        # Resolve language
        if language:
            try:
                lang = Language(language.lower())
            except ValueError:
                lang = Language.UNKNOWN
        else:
            lang = self.detect_language(code)

        self._execution_count += 1

        # Simulated execution — in production, this would run in the container
        result = self._simulate_execution(code, lang)
        result.duration_seconds = round(time.time() - start, 4)
        result.language = lang
        return result.to_dict()

    def _simulate_execution(self, code: str, language: Language) -> ExecutionResult:
        """Simulate code execution with basic interpretation.

        This provides a realistic mock for testing. A real implementation
        would delegate to the container's language runtimes.
        """
        # Handle empty / whitespace
        stripped = code.strip()
        if not stripped:
            return ExecutionResult(exit_code=0, stdout="", stderr="")

        # Simulate syntax errors for obviously broken code
        if language == Language.PYTHON:
            return self._simulate_python(stripped)
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return self._simulate_js(stripped)
        elif language == Language.BASH:
            return self._simulate_bash(stripped)
        else:
            # Generic: return the code as a successful "echo"
            return ExecutionResult(
                exit_code=0,
                stdout=f"[{language.value}] executed successfully\n",
            )

    def _simulate_python(self, code: str) -> ExecutionResult:
        """Simulate basic Python execution."""
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        for line in code.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Match print("...") or print('...') or print(...)
            m = re.match(r'^print\((["\'])(.*)\1\)$', line_stripped)
            if m:
                stdout_lines.append(m.group(2))
            elif line_stripped.startswith("print("):
                # More complex print — just extract between parens roughly
                inner = line_stripped[6:].rstrip(")").strip()
                if inner.startswith(("'", '"')):
                    inner = inner[1:-1]
                stdout_lines.append(inner)
            elif line_stripped.startswith(("import ", "from ")):
                pass  # imports are fine
            elif line_stripped.startswith(("def ", "class ", "if ", "for ", "while ")):
                pass  # control flow — ignore in simulation
            elif "=" in line_stripped:
                pass  # assignments — ignore
            elif line_stripped.startswith("raise "):
                # Extract the exception message if present
                msg = line_stripped[6:].strip()
                m = re.match(r'(?:\w+\()?["\'](.+?)["\']\)?', msg)
                if m:
                    stderr_lines.append(m.group(1))
                else:
                    stderr_lines.append(msg)
                return ExecutionResult(exit_code=1, stdout="\n".join(stdout_lines), stderr="\n".join(stderr_lines))

        return ExecutionResult(
            exit_code=0,
            stdout="\n".join(stdout_lines) + ("\n" if stdout_lines else ""),
        )

    def _simulate_js(self, code: str) -> ExecutionResult:
        """Simulate basic JS/TS execution."""
        stdout_lines: list[str] = []

        for line in code.splitlines():
            s = line.strip()
            if not s or s.startswith("//"):
                continue
            m = re.match(r'^console\.log\((["\'])(.*)\1\);?$', s)
            if m:
                stdout_lines.append(m.group(2))

        return ExecutionResult(
            exit_code=0,
            stdout="\n".join(stdout_lines) + ("\n" if stdout_lines else ""),
        )

    def _simulate_bash(self, code: str) -> ExecutionResult:
        """Simulate basic bash execution."""
        stdout_lines: list[str] = []

        for line in code.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            m = re.match(r'^echo\s+["\']?(.+?)["\']?\s*$', s)
            if m:
                stdout_lines.append(m.group(1))

        return ExecutionResult(
            exit_code=0,
            stdout="\n".join(stdout_lines) + ("\n" if stdout_lines else ""),
        )

    def info(self) -> dict:
        """Return runtime info."""
        return {
            "execution_count": self._execution_count,
            "supported_languages": [l.value for l in Language if l != Language.UNKNOWN],
        }
