"""Default review rule templates seeded into the database on first run."""

from typing import Any

SeedTemplate = dict[str, Any]

DEFAULT_TEMPLATES: list[SeedTemplate] = [
    {
        "name": "Strict Security",
        "description": (
            "Security-first review: all agents enabled, security agent at maximum "
            "priority, low confidence threshold to catch subtle issues."
        ),
        "rules": {
            "agents": {
                "logic": {
                    "enabled": True,
                    "severity_threshold": "low",
                    "custom_instructions": "Flag any potential null dereference or unhandled error paths.",
                    "max_findings": 20,
                },
                "security": {
                    "enabled": True,
                    "severity_threshold": "low",
                    "custom_instructions": (
                        "Treat every user-controlled input as untrusted. "
                        "Flag injection risks, insecure deserialization, auth bypass, "
                        "and data-leakage patterns at any confidence level."
                    ),
                    "max_findings": 30,
                },
                "edge_case": {
                    "enabled": True,
                    "severity_threshold": "low",
                    "custom_instructions": "Include off-by-one, overflow, and race-condition edge cases.",
                    "max_findings": 20,
                },
                "convention": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
                "performance": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
            },
            "global": {
                "max_total_findings": 90,
                "min_confidence": 0.4,
                "language_hints": [],
                "ignore_patterns": [],
            },
        },
        "created_by": "system",
    },
    {
        "name": "Quick Scan",
        "description": (
            "Fast, focused review: only logic and security agents run, "
            "high confidence threshold, capped at 10 total findings."
        ),
        "rules": {
            "agents": {
                "logic": {
                    "enabled": True,
                    "severity_threshold": "high",
                    "custom_instructions": "",
                    "max_findings": 5,
                },
                "security": {
                    "enabled": True,
                    "severity_threshold": "high",
                    "custom_instructions": "",
                    "max_findings": 5,
                },
                "edge_case": {
                    "enabled": False,
                    "severity_threshold": "high",
                    "custom_instructions": "",
                    "max_findings": 0,
                },
                "convention": {
                    "enabled": False,
                    "severity_threshold": "high",
                    "custom_instructions": "",
                    "max_findings": 0,
                },
                "performance": {
                    "enabled": False,
                    "severity_threshold": "high",
                    "custom_instructions": "",
                    "max_findings": 0,
                },
            },
            "global": {
                "max_total_findings": 10,
                "min_confidence": 0.8,
                "language_hints": [],
                "ignore_patterns": ["*.test.*", "*.spec.*", "migrations/*"],
            },
        },
        "created_by": "system",
    },
    {
        "name": "Full Review",
        "description": (
            "Comprehensive review: all five agents enabled with balanced settings "
            "and default confidence threshold."
        ),
        "rules": {
            "agents": {
                "logic": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
                "security": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
                "edge_case": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
                "convention": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
                "performance": {
                    "enabled": True,
                    "severity_threshold": "medium",
                    "custom_instructions": "",
                    "max_findings": 10,
                },
            },
            "global": {
                "max_total_findings": 30,
                "min_confidence": 0.6,
                "language_hints": [],
                "ignore_patterns": ["*.test.*", "*.spec.*"],
            },
        },
        "created_by": "system",
    },
]


def get_default_templates() -> list[SeedTemplate]:
    """Return the list of built-in review rule templates."""
    return DEFAULT_TEMPLATES
