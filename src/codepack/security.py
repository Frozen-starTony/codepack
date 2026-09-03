"""
Security module for CodePack: Detects and redacts sensitive credentials and secrets.
"""

from dataclasses import dataclass
import re
from typing import List, Tuple


@dataclass
class SecurityFinding:
    rule_name: str
    line_number: int
    matched_snippet: str
    redacted_preview: str


@dataclass
class SecurityReport:
    findings: List[SecurityFinding]

    @property
    def has_secrets(self) -> bool:
        return len(self.findings) > 0


SECRET_PATTERNS = [
    (
        "OpenAI API Key",
        re.compile(r"\b(sk-[a-zA-Z0-9T3BlbkFJ]{20,}|sk-proj-[a-zA-Z0-9_\-]{20,})\b"),
        "[REDACTED_OPENAI_KEY]",
    ),
    (
        "Anthropic API Key",
        re.compile(r"\b(sk-ant-[a-zA-Z0-9_\-]{20,})\b"),
        "[REDACTED_ANTHROPIC_KEY]",
    ),
    (
        "Google API Key",
        re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,40})\b"),
        "[REDACTED_GOOGLE_API_KEY]",
    ),
    (
        "GitHub Personal Access Token",
        re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_\-]{30,})\b"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (
        "Slack Token",
        re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b"),
        "[REDACTED_SLACK_TOKEN]",
    ),
    (
        "AWS Access Key ID",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),
    (
        "Private Cryptographic Key",
        re.compile(
            r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (
        "Hardcoded Secret or Password",
        re.compile(
            r"""(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|jwt)\s*[:=]\s*(['"])([a-zA-Z0-9!@#$%^&*()_\-+={}\[\]|;:,.<>?/~`]{8,})\2"""
        ),
        r"\1 = \2[REDACTED_CREDENTIAL]\2",
    ),
]


def redact_secrets(content: str) -> Tuple[str, SecurityReport]:
    """
    Scans text content for sensitive tokens, redacting them and generating a report.
    """
    findings: List[SecurityFinding] = []
    redacted_content = content

    # Find findings with line numbers before applying replacements
    lines = content.splitlines()

    for rule_name, pattern, replacement in SECRET_PATTERNS:
        # Check line-by-line for report mapping
        for line_idx, line in enumerate(lines, start=1):
            for match in pattern.finditer(line):
                findings.append(
                    SecurityFinding(
                        rule_name=rule_name,
                        line_number=line_idx,
                        matched_snippet=match.group(0)[:20] + "..." if len(match.group(0)) > 20 else match.group(0),
                        redacted_preview=f"Line {line_idx}: {rule_name}",
                    )
                )

        # Replace in full content
        redacted_content = pattern.sub(replacement, redacted_content)

    return redacted_content, SecurityReport(findings=findings)
