"""Data models for RigCheck findings."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Finding:
    rule: str
    severity: Severity
    message: str
    details: Optional[str] = None


@dataclass
class CheckResult:
    rule_name: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """INFO만 있으면 PASS. Critical/Warning이 있으면 FAIL."""
        return all(f.severity == Severity.INFO for f in self.findings)


@dataclass
class Report:
    model_name: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.results)

    @property
    def critical_count(self) -> int:
        return sum(
            1 for r in self.results for f in r.findings
            if f.severity == Severity.CRITICAL
        )

    @property
    def warning_count(self) -> int:
        return sum(
            1 for r in self.results for f in r.findings
            if f.severity == Severity.WARNING
        )

    @property
    def info_count(self) -> int:
        return sum(
            1 for r in self.results for f in r.findings
            if f.severity == Severity.INFO
        )

    def summary(self) -> str:
        lines = [
            f"=== RigCheck Report: {self.model_name} ===",
            f"Total findings: {self.total_findings}",
            f"  Critical: {self.critical_count}",
            f"  Warning:  {self.warning_count}",
            f"  Info:     {self.info_count}",
            "",
        ]
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"[{status}] {result.rule_name} ({len(result.findings)} findings)")
            for f in result.findings:
                icon = {"critical": "!!!", "warning": " ! ", "info": " i "}[f.severity.value]
                lines.append(f"  [{icon}] {f.message}")
                if f.details:
                    lines.append(f"        {f.details}")
        return "\n".join(lines)
